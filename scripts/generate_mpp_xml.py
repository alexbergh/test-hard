"""Generate MS Project XML from PROJECT_PLAN.md task data.

Output: Мониторинг харденинга ПГ v2.xml
Open in MS Project -> File > Save As -> .mpp
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path


def add_business_days(start: datetime, days: int) -> datetime:
    """Return the date after adding *days* business days (Mon-Fri)."""
    if days == 0:
        return start
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def next_business_day(dt: datetime) -> datetime:
    """Advance to the next business day if dt falls on a weekend."""
    while dt.weekday() >= 5:
        dt += timedelta(days=1)
    return dt


def fmt_start(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT08:00:00")


def fmt_finish(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT17:00:00")


def fmt_duration(days: int) -> str:
    return f"PT{days * 8}H0M0S"


# ---------------------------------------------------------------------------
# Task data
# (id, name, duration_days, outline_level, predecessor_id, is_summary, resources, notes)
# ---------------------------------------------------------------------------
TASKS = [
    (1, "Комплексное решение для мониторинга харденинга", 0, 1, None, True, [], ""),
    # Phase 1
    (2, "Фаза 1: Архитектурная проработка", 0, 2, None, True, [], ""),
    (3, "Анализ и проработка замечаний к архдоку", 10, 3, None, False, ["ЦКГС"], "Доработка имеющейся фактуры"),
    (4, "Промежуточное демо", 1, 3, 3, False, ["ЦКГС", "ЦМРК"], "Демонстрация текущего состояния решения"),
    (5, "Внутреннее согласование скорректированной версии", 5, 3, 4, False, ["ЦКГС", "ЦМРК"],
     "С учётом результатов демо"),
    (6, "Сбор, анализ и доработка замечаний", 10, 3, 5, False, ["ЦКГС"], ""),
    (7, "Буфер фазы 1", 1, 3, 6, False, [], "Резерв на непредвиденные задержки"),
    # Phase 2
    (8, "Фаза 2: Подготовка пилотной среды", 0, 2, None, True, [], ""),
    (9, "Определение места и ресурсов для пилота", 3, 3, 7, False, ["ЦКГС", "ЦМРК"],
     "Выделение стенда, сети, доступов"),
    (10, "Развёртывание решения на стенде", 3, 3, 9, False, ["ЦКГС"],
     "Docker Compose / K8s, мониторинг стек"),
    (11, "Настройка интеграций с целевой инфраструктурой", 3, 3, 10, False, ["ЦКГС"],
     "Подключение кластеров, хостов, сеть"),
    (12, "Верификация развёртывания", 2, 3, 11, False, ["ЦКГС"], "Smoke-тесты, проверка компонентов"),
    (13, "Буфер фазы 2", 2, 3, 12, False, [], "Резерв на проблемы с инфраструктурой"),
    # Phase 3
    (14, "Фаза 3: Проведение пилота", 0, 2, None, True, [], ""),
    (15, "Проведение пилота", 8, 3, 13, False, ["ЦКГС"],
     "8 сценариев: discovery, hardening, scan, drift, image, monitoring, нагрузка, комплексный"),
    (16, "Доработка решения по результатам пилота", 5, 3, 15, False, ["ЦКГС"],
     "Исправление дефектов, доработка"),
    (17, "Валидация результатов", 3, 3, 16, False, ["ЦКГС"], "Повторная проверка по критериям"),
    (18, "Подготовка отчёта о пилоте", 2, 3, 17, False, ["ЦКГС"], "Метрики, выводы, рекомендации"),
    (19, "Внутреннее согласование результатов пилота", 5, 3, 18, False, ["ЦКГС", "ЦМРК"],
     "Утверждение доработанной версии"),
    # Phase 4
    (20, "Фаза 4: Архком РТЛабс", 0, 2, None, True, [], ""),
    (21, "Актуализация архдока, запись на архком", 5, 3, 19, False, ["ЦКГС"],
     "На основе согласованных результатов"),
    (22, "Представление решения на архкоме", 1, 3, 21, False, ["ЦКГС"], ""),
    (23, "Буфер (доработка по замечаниям архкома)", 2, 3, 22, False, ["ЦКГС"], "Если будут замечания"),
    # Phase 5
    (24, "Фаза 5: Ввод в эксплуатацию", 0, 2, None, True, [], ""),
    (25, "Подготовка эксплуатационной документации", 3, 3, 23, False, ["ЦКГС"],
     "Runbooks, инструкции, SLA"),
    (26, "Обучение и передача знаний", 2, 3, 25, False, ["ЦКГС"], "Операторы, администраторы"),
    (27, "Развёртывание в промышленной среде", 3, 3, 26, False, ["ЦКГС"], "С мониторингом процесса"),
    (28, "Приёмочное тестирование (UAT)", 2, 3, 27, False, ["ЦКГС", "ЦМРК"],
     "Подтверждение работоспособности"),
    (29, "Подписание акта ввода в эксплуатацию", 1, 2, 28, False, ["ЦКГС", "ЦМРК"],
     "Формальное завершение проекта"),
]

RESOURCES = {"ЦКГС": 1, "ЦМРК": 2}

PROJECT_START = datetime(2026, 2, 16)


def compute_dates():
    """Compute start/finish for every task based on predecessors."""
    dates = {}  # task_id -> (start, finish)

    for tid, name, dur, level, pred, is_summary, res, notes in TASKS:
        if is_summary:
            continue
        if pred is None:
            start = PROJECT_START
        else:
            _, pred_finish = dates[pred]
            start = next_business_day(pred_finish + timedelta(days=1))
        finish = add_business_days(start, dur - 1) if dur > 1 else start
        dates[tid] = (start, finish)

    # Task 29 is at outline level 2, direct child of task 1
    # Summary tasks: span their children
    summary_children = {
        2: [3, 4, 5, 6, 7],     # phase 1
        8: [9, 10, 11, 12, 13], # phase 2
        14: [15, 16, 17, 18, 19],  # phase 3
        20: [21, 22, 23],       # phase 4
        24: [25, 26, 27, 28],   # phase 5
        1: list(range(2, 30)),   # top-level summary (must be last)
    }
    # Process bottom-up
    for summary_id in [2, 8, 14, 20, 24, 1]:
        children = summary_children[summary_id]
        child_dates = [dates[c] for c in children if c in dates]
        if child_dates:
            earliest = min(d[0] for d in child_dates)
            latest = max(d[1] for d in child_dates)
            dates[summary_id] = (earliest, latest)

    return dates


def build_xml():
    """Build the MS Project XML document."""
    dates = compute_dates()

    project = ET.Element("Project")
    project.set("xmlns", "http://schemas.microsoft.com/project")

    ET.SubElement(project, "Name").text = "Мониторинг харденинга ПГ v2"
    ET.SubElement(project, "Title").text = "Комплексное решение для мониторинга харденинга"
    ET.SubElement(project, "StartDate").text = fmt_start(PROJECT_START)
    ET.SubElement(project, "FinishDate").text = fmt_finish(dates[1][1])
    ET.SubElement(project, "ScheduleFromStart").text = "1"
    ET.SubElement(project, "CalendarUID").text = "1"
    ET.SubElement(project, "DefaultStartTime").text = "08:00:00"
    ET.SubElement(project, "DefaultFinishTime").text = "17:00:00"
    ET.SubElement(project, "MinutesPerDay").text = "480"
    ET.SubElement(project, "MinutesPerWeek").text = "2400"
    ET.SubElement(project, "DaysPerMonth").text = "20"
    ET.SubElement(project, "CurrencyCode").text = "RUB"

    # ---- Calendar ----
    calendars = ET.SubElement(project, "Calendars")
    cal = ET.SubElement(calendars, "Calendar")
    ET.SubElement(cal, "UID").text = "1"
    ET.SubElement(cal, "Name").text = "Standard"
    ET.SubElement(cal, "IsBaseCalendar").text = "1"

    weekdays = ET.SubElement(cal, "WeekDays")
    # Sunday (1) - non-working
    wd = ET.SubElement(weekdays, "WeekDay")
    ET.SubElement(wd, "DayType").text = "1"
    ET.SubElement(wd, "DayWorking").text = "0"
    # Mon (2) - Fri (6) - working
    for day_type in range(2, 7):
        wd = ET.SubElement(weekdays, "WeekDay")
        ET.SubElement(wd, "DayType").text = str(day_type)
        ET.SubElement(wd, "DayWorking").text = "1"
        wts = ET.SubElement(wd, "WorkingTimes")
        wt1 = ET.SubElement(wts, "WorkingTime")
        ET.SubElement(wt1, "FromTime").text = "08:00:00"
        ET.SubElement(wt1, "ToTime").text = "12:00:00"
        wt2 = ET.SubElement(wts, "WorkingTime")
        ET.SubElement(wt2, "FromTime").text = "13:00:00"
        ET.SubElement(wt2, "ToTime").text = "17:00:00"
    # Saturday (7) - non-working
    wd = ET.SubElement(weekdays, "WeekDay")
    ET.SubElement(wd, "DayType").text = "7"
    ET.SubElement(wd, "DayWorking").text = "0"

    # ---- Tasks ----
    tasks_elem = ET.SubElement(project, "Tasks")

    # Task 0 - project summary (required)
    t0 = ET.SubElement(tasks_elem, "Task")
    ET.SubElement(t0, "UID").text = "0"
    ET.SubElement(t0, "ID").text = "0"
    ET.SubElement(t0, "Name").text = "Мониторинг харденинга ПГ v2"
    ET.SubElement(t0, "Type").text = "1"
    ET.SubElement(t0, "IsNull").text = "0"
    ET.SubElement(t0, "OutlineLevel").text = "0"
    ET.SubElement(t0, "OutlineNumber").text = "0"
    ET.SubElement(t0, "Summary").text = "1"
    ET.SubElement(t0, "Start").text = fmt_start(PROJECT_START)
    ET.SubElement(t0, "Finish").text = fmt_finish(dates[1][1])
    ET.SubElement(t0, "Duration").text = fmt_duration(81)
    ET.SubElement(t0, "ManualStart").text = fmt_start(PROJECT_START)
    ET.SubElement(t0, "ManualFinish").text = fmt_finish(dates[1][1])

    for tid, name, dur, level, pred, is_summary, res_names, notes in TASKS:
        t = ET.SubElement(tasks_elem, "Task")
        ET.SubElement(t, "UID").text = str(tid)
        ET.SubElement(t, "ID").text = str(tid)
        ET.SubElement(t, "Name").text = name
        ET.SubElement(t, "Type").text = "1"
        ET.SubElement(t, "IsNull").text = "0"
        ET.SubElement(t, "OutlineLevel").text = str(level)
        ET.SubElement(t, "Summary").text = "1" if is_summary else "0"

        start_dt, finish_dt = dates[tid]
        ET.SubElement(t, "Start").text = fmt_start(start_dt)
        ET.SubElement(t, "Finish").text = fmt_finish(finish_dt)

        if is_summary:
            child_dur = 0
            # Calculate actual working days between start and finish
            d = start_dt
            while d <= finish_dt:
                if d.weekday() < 5:
                    child_dur += 1
                d += timedelta(days=1)
            ET.SubElement(t, "Duration").text = fmt_duration(child_dur)
        else:
            ET.SubElement(t, "Duration").text = fmt_duration(dur)

        ET.SubElement(t, "DurationFormat").text = "7"  # days
        ET.SubElement(t, "ManualStart").text = fmt_start(start_dt)
        ET.SubElement(t, "ManualFinish").text = fmt_finish(finish_dt)
        ET.SubElement(t, "ConstraintType").text = "0"  # ASAP
        ET.SubElement(t, "CalendarUID").text = "-1"

        if notes:
            ET.SubElement(t, "Notes").text = notes

        if pred is not None:
            pl = ET.SubElement(t, "PredecessorLink")
            ET.SubElement(pl, "PredecessorUID").text = str(pred)
            ET.SubElement(pl, "Type").text = "1"  # Finish-to-Start
            ET.SubElement(pl, "CrossProject").text = "0"
            ET.SubElement(pl, "LinkLag").text = "0"
            ET.SubElement(pl, "LagFormat").text = "7"

    # ---- Resources ----
    resources_elem = ET.SubElement(project, "Resources")
    # Resource 0 is internal
    r0 = ET.SubElement(resources_elem, "Resource")
    ET.SubElement(r0, "UID").text = "0"
    ET.SubElement(r0, "ID").text = "0"
    ET.SubElement(r0, "Name").text = ""

    for res_name, res_uid in RESOURCES.items():
        r = ET.SubElement(resources_elem, "Resource")
        ET.SubElement(r, "UID").text = str(res_uid)
        ET.SubElement(r, "ID").text = str(res_uid)
        ET.SubElement(r, "Name").text = res_name
        ET.SubElement(r, "Type").text = "1"  # Work resource
        ET.SubElement(r, "IsNull").text = "0"
        ET.SubElement(r, "MaxUnits").text = "1.0"
        ET.SubElement(r, "CalendarUID").text = "1"

    # ---- Assignments ----
    assignments_elem = ET.SubElement(project, "Assignments")
    assign_uid = 0
    for tid, name, dur, level, pred, is_summary, res_names, notes in TASKS:
        if is_summary:
            continue
        for res_name in res_names:
            res_uid = RESOURCES.get(res_name)
            if res_uid is None:
                continue
            a = ET.SubElement(assignments_elem, "Assignment")
            ET.SubElement(a, "UID").text = str(assign_uid)
            ET.SubElement(a, "TaskUID").text = str(tid)
            ET.SubElement(a, "ResourceUID").text = str(res_uid)
            start_dt, finish_dt = dates[tid]
            ET.SubElement(a, "Start").text = fmt_start(start_dt)
            ET.SubElement(a, "Finish").text = fmt_finish(finish_dt)
            ET.SubElement(a, "Units").text = "1"
            work_hours = dur * 8
            ET.SubElement(a, "Work").text = f"PT{work_hours}H0M0S"
            assign_uid += 1

    return project


def write_xml(project, output_path):
    """Write pretty-printed XML to file."""
    rough = ET.tostring(project, encoding="unicode", xml_declaration=False)
    from xml.dom.minidom import parseString
    dom = parseString(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>{rough}')
    pretty = dom.toprettyxml(indent="  ", encoding="UTF-8")
    # Remove extra xml declaration from toprettyxml
    lines = pretty.decode("utf-8").split("\n")
    # toprettyxml adds its own declaration, keep only one
    with open(output_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        for line in lines[1:]:  # skip the auto-generated declaration
            f.write(line + "\n")


def main():
    repo_root = Path(__file__).resolve().parent.parent
    output = repo_root / "Мониторинг харденинга ПГ v2.xml"
    project = build_xml()
    write_xml(project, output)

    dates = compute_dates()
    print(f"Generated: {output}")
    print(f"Project: {fmt_start(PROJECT_START)} - {fmt_finish(dates[1][1])}")
    print(f"Tasks: {len(TASKS)}")
    print()
    print("Schedule:")
    for tid, name, dur, level, pred, is_summary, res, notes in TASKS:
        s, f = dates[tid]
        indent = "  " * (level - 1)
        marker = "[S]" if is_summary else "   "
        res_str = ", ".join(res) if res else ""
        print(f"  {tid:2d} {marker} {indent}{name:<55s} {s.strftime('%d.%m.%y')} - {f.strftime('%d.%m.%y')}  {res_str}")


if __name__ == "__main__":
    main()
