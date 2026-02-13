#!/usr/bin/env python3
"""
Генератор диаграмм для документа архитектуры test-hard
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


def create_sequence_diagram():
    """
    Создать Sequence диаграмму процесса сканирования безопасности (5.1)
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Заголовок
    ax.text(7, 11.5, 'SEQUENCE DIAGRAM: Security Scanning Process', 
            fontsize=14, fontweight='bold', ha='center', 
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#4472C4', edgecolor='none'),
            color='white')
    
    # Участники (акторы)
    actors = ['User', 'Dashboard', 'Scanner', 'DockerProxy', 'Target']
    actor_x = [1, 3.5, 6, 9, 12]
    actor_colors = ['#70AD47', '#4472C4', '#ED7D31', '#7030A0', '#C00000']
    
    for i, (name, x, color) in enumerate(zip(actors, actor_x, actor_colors)):
        # Прямоугольник актора
        rect = FancyBboxPatch((x-0.6, 10.2), 1.2, 0.6, 
                               boxstyle="round,pad=0.05", 
                               facecolor=color, edgecolor='black', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, 10.5, name, fontsize=9, fontweight='bold', ha='center', va='center', color='white')
        
        # Вертикальная линия жизни
        ax.plot([x, x], [10.2, 1], color='gray', linestyle='--', linewidth=1)
    
    # Сообщения (стрелки)
    messages = [
        (1, 3.5, 9.5, '1. Start Scan', '#70AD47'),
        (3.5, 6, 8.8, '2. API Call', '#4472C4'),
        (6, 9, 8.1, '3. Get Containers', '#ED7D31'),
        (9, 6, 7.4, '4. Container IDs', '#7030A0'),
        (6, 9, 6.7, '5. Exec Scan', '#ED7D31'),
        (9, 12, 6.0, '6. Execute OpenSCAP/Lynis', '#7030A0'),
        (12, 9, 5.3, '7. Return Results', '#C00000'),
        (9, 6, 4.6, '8. Scan Results', '#7030A0'),
        (6, 3.5, 3.9, '9. Parse Results', '#ED7D31'),
        (3.5, 3.5, 3.2, '10. Store Metrics (Prometheus)', '#4472C4'),
        (3.5, 1, 2.5, '11. Status OK', '#4472C4'),
    ]
    
    for x1, x2, y, label, color in messages:
        # Стрелка
        if x1 < x2:
            ax.annotate('', xy=(x2-0.1, y), xytext=(x1+0.1, y),
                       arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
            ax.text((x1+x2)/2, y+0.15, label, fontsize=8, ha='center', va='bottom', color='#333333')
        elif x1 > x2:
            ax.annotate('', xy=(x2+0.1, y), xytext=(x1-0.1, y),
                       arrowprops=dict(arrowstyle='->', color=color, lw=1.5, linestyle='--'))
            ax.text((x1+x2)/2, y+0.15, label, fontsize=8, ha='center', va='bottom', color='#333333')
        else:
            # Self-call
            ax.annotate('', xy=(x1+0.5, y-0.3), xytext=(x1+0.5, y),
                       arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
            ax.plot([x1, x1+0.5, x1+0.5], [y, y, y-0.3], color=color, lw=1.5)
            ax.text(x1+0.6, y-0.15, label, fontsize=7, ha='left', va='center', color='#333333')
    
    # Подпись
    ax.text(7, 0.3, 'Рисунок 5.1 — Sequence диаграмма сканирования безопасности', 
            fontsize=10, ha='center', style='italic', color='#666666')
    
    plt.tight_layout()
    plt.savefig('diagram_5_1_sequence_scanning.png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print('Сохранено: diagram_5_1_sequence_scanning.png')


def create_dataflow_diagram():
    """
    Создать Data Flow диаграмму мониторинга (5.2)
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 14)
    ax.axis('off')
    
    # Заголовок
    ax.text(7, 13.5, 'DATA FLOW: Monitoring & Alerting', 
            fontsize=14, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#4472C4', edgecolor='none'),
            color='white')
    
    # Компоненты
    components = {
        'targets': {'pos': (7, 12), 'label': 'Targets\n(Scanners)', 'color': '#70AD47'},
        'telegraf': {'pos': (3, 10), 'label': 'Telegraf\n(Collector)', 'color': '#ED7D31'},
        'prometheus': {'pos': (7, 10), 'label': 'Prometheus\n(TSDB)', 'color': '#C00000'},
        'alertmanager': {'pos': (11, 10), 'label': 'Alertmanager\n(Routing)', 'color': '#7030A0'},
        'grafana': {'pos': (3, 7), 'label': 'Grafana\n(Dashboards)', 'color': '#4472C4'},
        'loki': {'pos': (7, 7), 'label': 'Loki\n(Logs)', 'color': '#00B0F0'},
        'notifications': {'pos': (11, 7), 'label': 'Notifications\n(Webhook, Email)', 'color': '#FFC000'},
        'promtail': {'pos': (7, 4), 'label': 'Promtail\n(Log Shipper)', 'color': '#00B050'},
        'containers': {'pos': (7, 1.5), 'label': 'Container\nLogs', 'color': '#808080'},
    }
    
    for key, comp in components.items():
        x, y = comp['pos']
        rect = FancyBboxPatch((x-1, y-0.5), 2, 1, 
                               boxstyle="round,pad=0.1", 
                               facecolor=comp['color'], edgecolor='black', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y, comp['label'], fontsize=9, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Стрелки с подписями
    arrows = [
        # (from, to, label, curved)
        ('targets', 'telegraf', 'Metrics\n(pull 15s)', False),
        ('telegraf', 'prometheus', 'scrape', False),
        ('prometheus', 'alertmanager', 'alerts', False),
        ('prometheus', 'grafana', 'query', True),
        ('loki', 'grafana', 'query', False),
        ('alertmanager', 'notifications', '', False),
        ('promtail', 'loki', 'logs', False),
        ('containers', 'promtail', '', False),
    ]
    
    for from_key, to_key, label, curved in arrows:
        x1, y1 = components[from_key]['pos']
        x2, y2 = components[to_key]['pos']
        
        # Adjust start/end points based on direction
        if y1 > y2:  # Going down
            y1 -= 0.5
            y2 += 0.5
        elif y1 < y2:  # Going up
            y1 += 0.5
            y2 -= 0.5
        elif x1 < x2:  # Going right
            x1 += 1
            x2 -= 1
        else:  # Going left
            x1 -= 1
            x2 += 1
        
        if curved:
            style = "arc3,rad=-0.3"
        else:
            style = "arc3,rad=0"
        
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5,
                                   connectionstyle=style))
        
        if label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            if curved:
                mid_x -= 0.5
            ax.text(mid_x, mid_y, label, fontsize=8, ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.8))
    
    # Легенда потоков
    legend_items = [
        ('Metrics Flow', '#ED7D31'),
        ('Logs Flow', '#00B050'),
        ('Alert Flow', '#7030A0'),
        ('Query Flow', '#4472C4'),
    ]
    
    for i, (text, color) in enumerate(legend_items):
        ax.add_patch(FancyBboxPatch((0.5, 3-i*0.6), 0.3, 0.3, 
                                     boxstyle="round,pad=0.02", facecolor=color))
        ax.text(1, 3.15-i*0.6, text, fontsize=8, va='center')
    
    # Подпись
    ax.text(7, 0.3, 'Рисунок 5.2 — Data Flow диаграмма мониторинга', 
            fontsize=10, ha='center', style='italic', color='#666666')
    
    plt.tight_layout()
    plt.savefig('diagram_5_2_dataflow_monitoring.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print('Сохранено: diagram_5_2_dataflow_monitoring.png')


def create_docker_compose_diagram():
    """
    Создать Deployment диаграмму Docker Compose (6.1)
    """
    fig, ax = plt.subplots(1, 1, figsize=(16, 14))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # Заголовок
    ax.text(8, 15.5, 'DEPLOYMENT DIAGRAM: Docker Compose Environment', 
            fontsize=14, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#4472C4', edgecolor='none'),
            color='white')
    
    # HOST контейнер (внешняя рамка)
    host_rect = FancyBboxPatch((0.5, 1), 15, 13.5, 
                                boxstyle="round,pad=0.1", 
                                facecolor='#F0F0F0', edgecolor='#333333', linewidth=2)
    ax.add_patch(host_rect)
    ax.text(8, 14.2, 'HOST', fontsize=12, fontweight='bold', ha='center', color='#333333')
    
    # Network: default (верхняя сеть)
    default_net = FancyBboxPatch((1, 8), 14, 5.8, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor='#E6F3FF', edgecolor='#4472C4', linewidth=1.5)
    ax.add_patch(default_net)
    ax.text(8, 13.5, 'Network: default', fontsize=10, fontweight='bold', ha='center', color='#4472C4')
    
    # Верхний ряд контейнеров (мониторинг)
    top_containers = [
        {'name': 'prometheus', 'port': ':9090', 'res': '1CPU/1GB', 'color': '#C00000', 'x': 2.5},
        {'name': 'grafana', 'port': ':3000', 'res': '0.5CPU/512M', 'color': '#4472C4', 'x': 5.5},
        {'name': 'loki', 'port': ':3100', 'res': '0.5CPU/512M', 'color': '#00B0F0', 'x': 8.5},
        {'name': 'promtail', 'port': '', 'res': '0.25CPU/256M', 'color': '#00B050', 'x': 11.5},
    ]
    
    for cont in top_containers:
        rect = FancyBboxPatch((cont['x']-1, 11.5), 2, 1.5, 
                               boxstyle="round,pad=0.05", 
                               facecolor=cont['color'], edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(cont['x'], 12.5, cont['name'], fontsize=9, fontweight='bold', 
                ha='center', va='center', color='white')
        ax.text(cont['x'], 12.0, cont['port'], fontsize=8, ha='center', va='center', color='white')
        ax.text(cont['x'], 11.7, cont['res'], fontsize=7, ha='center', va='center', color='#EEEEEE')
    
    # Средний ряд контейнеров
    mid_containers = [
        {'name': 'alertmanager', 'port': ':9093', 'res': '0.25CPU/128M', 'color': '#7030A0', 'x': 2.5},
        {'name': 'telegraf', 'port': ':9091', 'res': '0.5CPU/256M', 'color': '#ED7D31', 'x': 5.5},
        {'name': 'openscap-scanner', 'port': '', 'res': '1CPU/512M', 'color': '#70AD47', 'x': 8.5},
    ]
    
    for cont in mid_containers:
        rect = FancyBboxPatch((cont['x']-1, 9.5), 2, 1.5, 
                               boxstyle="round,pad=0.05", 
                               facecolor=cont['color'], edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(cont['x'], 10.5, cont['name'], fontsize=8, fontweight='bold', 
                ha='center', va='center', color='white')
        ax.text(cont['x'], 10.0, cont['port'], fontsize=8, ha='center', va='center', color='white')
        ax.text(cont['x'], 9.7, cont['res'], fontsize=7, ha='center', va='center', color='#EEEEEE')
    
    # Lynis scanner
    rect = FancyBboxPatch((1.5, 8.3), 2, 0.9, 
                           boxstyle="round,pad=0.05", 
                           facecolor='#70AD47', edgecolor='black', linewidth=1)
    ax.add_patch(rect)
    ax.text(2.5, 8.9, 'lynis-scan', fontsize=8, fontweight='bold', ha='center', va='center', color='white')
    ax.text(2.5, 8.5, '1CPU/512M', fontsize=7, ha='center', va='center', color='#EEEEEE')
    
    # Network: scanner-net
    scanner_net = FancyBboxPatch((1, 4.5), 14, 3, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor='#FFF2CC', edgecolor='#ED7D31', linewidth=1.5)
    ax.add_patch(scanner_net)
    ax.text(8, 7.2, 'Network: scanner-net', fontsize=10, fontweight='bold', ha='center', color='#ED7D31')
    
    # Docker Proxy
    rect = FancyBboxPatch((6.5, 5.5), 3, 1.2, 
                           boxstyle="round,pad=0.05", 
                           facecolor='#7030A0', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(8, 6.3, 'docker-proxy', fontsize=9, fontweight='bold', ha='center', va='center', color='white')
    ax.text(8, 5.9, ':2375  |  0.25CPU/128M', fontsize=8, ha='center', va='center', color='#EEEEEE')
    
    # Стрелки к docker-proxy
    ax.annotate('', xy=(6.5, 6.1), xytext=(2.5, 8.3),
               arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(9.5, 6.1), xytext=(8.5, 9.5),
               arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    
    # Target Containers
    target_box = FancyBboxPatch((1.5, 1.5), 13, 2.5, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor='#D9D9D9', edgecolor='#666666', linewidth=1.5)
    ax.add_patch(target_box)
    ax.text(8, 3.7, 'TARGET CONTAINERS (sleep infinity)', fontsize=10, fontweight='bold', 
            ha='center', va='center', color='#333333')
    
    # Target containers
    targets = [
        {'name': 'fedora', 'ver': ':40', 'x': 3},
        {'name': 'debian', 'ver': ':12', 'x': 5.5},
        {'name': 'centos', 'ver': 'strm:9', 'x': 8},
        {'name': 'ubuntu', 'ver': ':22.04', 'x': 10.5},
        {'name': 'alt linux', 'ver': '', 'x': 13},
    ]
    
    for t in targets:
        rect = FancyBboxPatch((t['x']-0.8, 1.8), 1.6, 1.4, 
                               boxstyle="round,pad=0.05", 
                               facecolor='#808080', edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(t['x'], 2.7, t['name'], fontsize=8, fontweight='bold', ha='center', va='center', color='white')
        ax.text(t['x'], 2.2, t['ver'], fontsize=7, ha='center', va='center', color='#EEEEEE')
    
    # Стрелка от docker-proxy к targets
    ax.annotate('', xy=(8, 4), xytext=(8, 5.5),
               arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    
    # Информация о volumes и ports
    ax.text(8, 0.8, 'VOLUMES: prometheus-data, grafana-data, loki-data, ./reports', 
            fontsize=9, ha='center', color='#333333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#E2EFDA', edgecolor='#70AD47'))
    ax.text(8, 0.3, 'PORTS: 9090 (Prometheus), 3000 (Grafana), 9093 (Alertmanager), 3100 (Loki)', 
            fontsize=9, ha='center', color='#666666')
    
    plt.tight_layout()
    plt.savefig('diagram_6_1_docker_compose.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print('Сохранено: diagram_6_1_docker_compose.png')


def create_kubernetes_diagram():
    """
    Создать Deployment диаграмму Kubernetes (6.2)
    """
    fig, ax = plt.subplots(1, 1, figsize=(16, 14))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # Заголовок
    ax.text(8, 15.5, 'DEPLOYMENT DIAGRAM: Kubernetes Environment', 
            fontsize=14, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#326CE5', edgecolor='none'),
            color='white')
    
    # KUBERNETES CLUSTER (внешняя рамка)
    cluster_rect = FancyBboxPatch((0.5, 0.5), 15, 14.5, 
                                   boxstyle="round,pad=0.1", 
                                   facecolor='#F5F5F5', edgecolor='#326CE5', linewidth=2)
    ax.add_patch(cluster_rect)
    ax.text(8, 14.7, 'KUBERNETES CLUSTER', fontsize=12, fontweight='bold', ha='center', color='#326CE5')
    
    # Namespace: monitoring
    ns_rect = FancyBboxPatch((1, 3), 14, 11.3, 
                              boxstyle="round,pad=0.1", 
                              facecolor='#E8F4FD', edgecolor='#0D47A1', linewidth=1.5)
    ax.add_patch(ns_rect)
    ax.text(8, 14, 'Namespace: monitoring', fontsize=11, fontweight='bold', ha='center', color='#0D47A1')
    
    # Network Policies
    np_rect = FancyBboxPatch((1.5, 11.5), 13, 2.2, 
                              boxstyle="round,pad=0.1", 
                              facecolor='#FFEBEE', edgecolor='#C62828', linewidth=1)
    ax.add_patch(np_rect)
    ax.text(8, 13.4, 'Network Policies', fontsize=10, fontweight='bold', ha='center', color='#C62828')
    
    policies = [
        '• default-deny-all (Deny all by default)',
        '• allow-grafana (Ingress + Prometheus egress)',
        '• allow-prometheus (Telegraf scrape + Alertmanager egress)',
        '• allow-telegraf (Prometheus scrape ingress)',
        '• allow-alertmanager (Prometheus ingress + external egress)',
    ]
    for i, policy in enumerate(policies):
        ax.text(2, 13.0 - i*0.35, policy, fontsize=8, va='center', color='#333333')
    
    # Deployments
    deployments = [
        {'name': 'prometheus', 'color': '#C00000', 'x': 2.5},
        {'name': 'grafana', 'color': '#4472C4', 'x': 5.5},
        {'name': 'telegraf', 'color': '#ED7D31', 'x': 8.5},
        {'name': 'alertmgr', 'color': '#7030A0', 'x': 11.5},
    ]
    
    for dep in deployments:
        # Deployment box
        rect = FancyBboxPatch((dep['x']-1.2, 9.5), 2.4, 1.5, 
                               boxstyle="round,pad=0.05", 
                               facecolor=dep['color'], edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(dep['x'], 10.5, 'Deployment', fontsize=8, ha='center', va='center', color='white')
        ax.text(dep['x'], 10.1, dep['name'], fontsize=9, fontweight='bold', ha='center', va='center', color='white')
        ax.text(dep['x'], 9.7, 'replicas: 1', fontsize=7, ha='center', va='center', color='#EEEEEE')
        
        # Стрелка вниз
        ax.annotate('', xy=(dep['x'], 8.3), xytext=(dep['x'], 9.5),
                   arrowprops=dict(arrowstyle='->', color='#333333', lw=1))
        
        # Service box
        rect = FancyBboxPatch((dep['x']-1.2, 7.3), 2.4, 1, 
                               boxstyle="round,pad=0.05", 
                               facecolor='#00B050', edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(dep['x'], 8.0, 'Service', fontsize=8, ha='center', va='center', color='white')
        ax.text(dep['x'], 7.6, 'ClusterIP', fontsize=7, ha='center', va='center', color='#EEEEEE')
    
    # Порты под сервисами
    ports = [':9090', ':3000', ':9091', ':9093']
    for dep, port in zip(deployments, ports):
        ax.text(dep['x'], 7.0, port, fontsize=8, fontweight='bold', ha='center', color='#333333')
    
    # ConfigMaps
    cm_rect = FancyBboxPatch((1.5, 5), 13, 1.6, 
                              boxstyle="round,pad=0.1", 
                              facecolor='#FFF3E0', edgecolor='#E65100', linewidth=1)
    ax.add_patch(cm_rect)
    ax.text(8, 6.3, 'ConfigMaps', fontsize=10, fontweight='bold', ha='center', color='#E65100')
    
    configs = [
        ('prometheus-config', 'prometheus.yml, alert.rules.yml'),
        ('grafana-datasources', 'datasource configuration'),
        ('telegraf-config', 'telegraf.conf'),
    ]
    for i, (name, desc) in enumerate(configs):
        ax.text(2 + i*4.5, 5.6, f'• {name}', fontsize=8, va='center', fontweight='bold', color='#333333')
        ax.text(2 + i*4.5, 5.25, f'  ({desc})', fontsize=7, va='center', color='#666666')
    
    # PersistentVolumeClaims
    pvc_rect = FancyBboxPatch((1.5, 3.3), 13, 1.4, 
                               boxstyle="round,pad=0.1", 
                               facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=1)
    ax.add_patch(pvc_rect)
    ax.text(8, 4.4, 'PersistentVolumeClaims', fontsize=10, fontweight='bold', ha='center', color='#2E7D32')
    ax.text(4, 3.8, '• prometheus-data-pvc (10Gi)', fontsize=9, va='center', color='#333333')
    ax.text(10, 3.8, '• grafana-data-pvc (5Gi)', fontsize=9, va='center', color='#333333')
    
    # ArgoCD
    argo_rect = FancyBboxPatch((1, 0.8), 14, 2.2, 
                                boxstyle="round,pad=0.1", 
                                facecolor='#FCE4EC', edgecolor='#AD1457', linewidth=1.5)
    ax.add_patch(argo_rect)
    ax.text(8, 2.7, 'ArgoCD', fontsize=11, fontweight='bold', ha='center', color='#AD1457')
    
    argo_apps = [
        ('application-dev.yaml', 'auto-sync enabled', '#4CAF50'),
        ('application-staging.yaml', 'auto-sync enabled', '#FF9800'),
        ('application-prod.yaml', 'manual sync, auto-prune disabled', '#F44336'),
    ]
    for i, (name, desc, color) in enumerate(argo_apps):
        ax.add_patch(FancyBboxPatch((2 + i*4.3, 1.2), 3.8, 1.2, 
                                     boxstyle="round,pad=0.05", facecolor=color, alpha=0.3))
        ax.text(3.9 + i*4.3, 2.0, f'• {name}', fontsize=8, va='center', fontweight='bold', color='#333333')
        ax.text(3.9 + i*4.3, 1.5, f'  ({desc})', fontsize=7, va='center', color='#666666')
    
    plt.tight_layout()
    plt.savefig('diagram_6_2_kubernetes.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print('Сохранено: diagram_6_2_kubernetes.png')


if __name__ == '__main__':
    print('Генерация диаграмм...')
    create_sequence_diagram()
    create_dataflow_diagram()
    create_docker_compose_diagram()
    create_kubernetes_diagram()
    print('Готово!')
