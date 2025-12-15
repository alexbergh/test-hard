#!/usr/bin/env bash
set -euo pipefail

IFS=' ' read -r -a targets <<< "${TARGET_CONTAINERS:-}"

if [ ${#targets[@]} -eq 0 ]; then
  echo "No target containers provided via TARGET_CONTAINERS" >&2
  exit 1
fi

mkdir -p /reports/openscap

PROFILE="xccdf_org.ssgproject.content_profile_standard"

install_openscap() {
  local name="$1"
  case "$name" in
    target-fedora)
      docker exec "$name" sh -c "dnf -y install openscap-scanner scap-security-guide 2>&1 | grep -v 'already installed' || true"
      ;;
    target-centos)
      docker exec "$name" sh -c "dnf -y install openscap-scanner scap-security-guide 2>&1 | grep -v 'already installed' || true"
      ;;
    target-debian|target-ubuntu)
      # For Debian/Ubuntu install openscap packages inside the target so
      # scans can be executed there in a consistent way
      docker exec "$name" sh -c "apt-get update >/dev/null 2>&1 || true; \
        if command -v add-apt-repository >/dev/null 2>&1; then \
          add-apt-repository -y universe >/dev/null 2>&1 || true; \
        else \
          apt-get install -y --no-install-recommends software-properties-common >/dev/null 2>&1 || true; \
          add-apt-repository -y universe >/dev/null 2>&1 || true; \
        fi; \
        apt-get update && apt-get install -y --no-install-recommends openscap-scanner scap-security-guide || true"

      if ! docker exec "$name" command -v oscap >/dev/null 2>&1; then
        echo "OpenSCAP not available in $name after install attempt; skipping" >&2
        return 2
      fi
      ;;
    *)
      echo "Unknown container $name for OpenSCAP install; skipping" >&2
      return 2
      ;;
  esac
}

get_datastream() {
  local name="$1"
  case "$name" in
    target-fedora)
      echo "/usr/share/xml/scap/ssg/content/ssg-fedora-ds.xml"
      ;;
    target-centos)
      echo "/usr/share/xml/scap/ssg/content/ssg-cs9-ds.xml"
      ;;
    target-debian)
      # РџСЂРѕР±СѓРµРј СЂР°Р·РЅС‹Рµ РїСѓС‚Рё РґР»СЏ datastream
      echo "/usr/share/xml/scap/ssg/content/ssg-debian12-ds.xml"
      ;;
    target-ubuntu)
      # РџСЂРѕР±СѓРµРј СЂР°Р·РЅС‹Рµ РїСѓС‚Рё РґР»СЏ datastream
      echo "/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml"
      ;;
    *)
      echo ""
      ;;
  esac
}

scan_container() {
  local name="$1"
  local datastream
  datastream=$(get_datastream "$name")

  if [ -z "$datastream" ]; then
    echo "No datastream mapping for $name, skipping" >&2
    return 0
  fi

  # РџСЂРѕРІРµСЂРёС‚СЊ С‡С‚Рѕ datastream СЃСѓС‰РµСЃС‚РІСѓРµС‚, РёР»Рё РЅР°Р№С‚Рё Р°Р»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Р№ РїСѓС‚СЊ
  if ! docker exec "$name" test -f "$datastream" 2>/dev/null; then
    echo "Primary datastream $datastream not found, searching alternatives..." >&2

    # РСЃРєР°С‚СЊ datastream С„Р°Р№Р»С‹ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё
    local found_datastream
    found_datastream=$(docker exec "$name" find /usr -name "*ssg*ds.xml" -type f 2>/dev/null | head -1 || true)

    if [ -z "$found_datastream" ]; then
      echo "No datastream files found in $name, skipping" >&2
      return 0
    fi

    datastream="$found_datastream"
    echo "Found alternative datastream: $datastream" >&2
  fi

  local result_file="/tmp/openscap-results.xml"
  local report_file="/tmp/openscap-report.html"

  echo "[OpenSCAP] Scanning $name using $datastream" >&2

  # Р—Р°РїСѓСЃС‚РёС‚СЊ СЃРєР°РЅРёСЂРѕРІР°РЅРёРµ РІРЅСѓС‚СЂРё РєРѕРЅС‚РµР№РЅРµСЂР°
  # Make sure requested profile exists in datastream; if not, pick a fallback
  available_profiles=$(docker exec "$name" oscap info "$datastream" 2>/dev/null | grep -Eo 'Profile ID: .*' | sed -E 's/(Profile ID: )//' || true)
  if [[ -n "$available_profiles" ]]; then
    if ! echo "$available_profiles" | grep -q "^${PROFILE}$"; then
      echo "Requested profile ${PROFILE} not present in datastream; selecting fallback" >&2
      if echo "$available_profiles" | grep -q "^xccdf_org.ssgproject.content_profile_standard$"; then
        PROFILE="xccdf_org.ssgproject.content_profile_standard"
      else
        PROFILE=$(echo "$available_profiles" | head -n1)
      fi
      echo "Using profile: ${PROFILE}" >&2
    fi
  else
    echo "No profiles discovered in datastream, proceeding with requested profile: ${PROFILE}" >&2
  fi

  # Run the scan. Prefer running oscap inside the target container; if oscap is
  # not available in the target, fetch the datastream and run oscap locally
  # inside this scanner container.
  if docker exec "$name" command -v oscap >/dev/null 2>&1; then
    if ! docker exec "$name" oscap xccdf eval \
      --profile "$PROFILE" \
      --results "$result_file" \
      --report "$report_file" \
      "$datastream"; then
      echo "[OpenSCAP] oscap exited non-zero for $name (will still try to collect outputs)" >&2
    fi
  else
    tmp_ds="/tmp/ssg-${name}.xml"
    # try to copy datastream content via docker exec cat
    if docker exec "$name" sh -c "cat \"$datastream\"" >"$tmp_ds" 2>/dev/null; then
      oscap xccdf eval \
        --profile "$PROFILE" \
        --results "$result_file" \
        --report "$report_file" \
        "$tmp_ds" >/dev/null 2>&1 || true
      rm -f "$tmp_ds" || true
    else
      echo "Failed to fetch datastream from $name: $datastream" >&2
    fi
  fi

  # Attempt to copy outputs even if the command exited non-zero
  local copied_any=0
  if ! docker exec "$name" test -s "$result_file" 2>/dev/null; then
    echo "[OpenSCAP] Result XML not found in $name at $result_file" >&2
  fi
  if ! docker exec "$name" test -s "$report_file" 2>/dev/null; then
    echo "[OpenSCAP] Report HTML not found in $name at $report_file" >&2
  fi
  if docker cp "$name:$result_file" "/reports/openscap/${name}.xml" 2>/dev/null; then
    copied_any=1
  else
    if docker exec "$name" sh -c "cat '$result_file'" >"/reports/openscap/${name}.xml" 2>/dev/null; then
      copied_any=1
    else
      echo "Failed to copy XML from $name:$result_file" >&2
    fi
  fi

  if docker cp "$name:$report_file" "/reports/openscap/${name}.html" 2>/dev/null; then
    copied_any=1
  else
    if docker exec "$name" sh -c "cat '$report_file'" >"/reports/openscap/${name}.html" 2>/dev/null; then
      copied_any=1
    else
      echo "Failed to copy HTML from $name:$report_file" >&2
    fi
  fi

  if [[ $copied_any -eq 1 ]]; then
    extract_openscap_metrics "$name" "/reports/openscap/${name}.xml" || true
    echo "[OpenSCAP] Scan completed for $name" >&2
    return 0
  else
    echo "[OpenSCAP] Scan failed for $name (no outputs copied)" >&2
    return 1
  fi
}

extract_openscap_metrics() {
  local name="$1"
  local xml_file="$2"
  local metrics_file="/reports/openscap/${name}_metrics.prom"

  echo "[OpenSCAP] Extracting metrics for ${name}" >&2

  if [ ! -f "$xml_file" ]; then
    echo "[OpenSCAP] XML file not found: $xml_file" >&2
    return 1
  fi

  # РР·РІР»РµС‡СЊ РєРѕР»РёС‡РµСЃС‚РІРѕ passed, failed, notselected РїСЂР°РІРёР»
  local pass_count
  local fail_count
  # РСЃРїРѕР»СЊР·РѕРІР°С‚СЊ grep -o РґР»СЏ РїРѕРґСЃС‡РµС‚Р° РІСЃРµС… РІС…РѕР¶РґРµРЅРёР№
  pass_count=$(grep -o '<result>pass</result>' "$xml_file" 2>/dev/null | wc -l | tr -cd '0-9')
  fail_count=$(grep -o '<result>fail</result>' "$xml_file" 2>/dev/null | wc -l | tr -cd '0-9')

  # Р•СЃР»Рё РїСѓСЃС‚С‹Рµ, СѓСЃС‚Р°РЅРѕРІРёС‚СЊ 0
  pass_count=${pass_count:-0}
  fail_count=${fail_count:-0}

  # Р’С‹С‡РёСЃР»РёС‚СЊ score РёР· pass/fail
  local total=$((pass_count + fail_count))
  local score=0
  if [ "$total" -gt 0 ]; then
    score=$((pass_count * 100 / total))
  fi

  # РЎРѕР·РґР°С‚СЊ РѕСЃРЅРѕРІРЅРѕР№ Prometheus metrics С„Р°Р№Р»
  cat > "$metrics_file" <<EOF
# HELP openscap_pass_count OpenSCAP passed rules count
# TYPE openscap_pass_count gauge
openscap_pass_count{host="${name}"} ${pass_count}
# HELP openscap_fail_count OpenSCAP failed rules count
# TYPE openscap_fail_count gauge
openscap_fail_count{host="${name}"} ${fail_count}
# HELP openscap_score OpenSCAP compliance score
# TYPE openscap_score gauge
openscap_score{host="${name}"} ${score}
EOF

  # РЎРѕР·РґР°С‚СЊ РґРµС‚Р°Р»СЊРЅС‹Р№ С„Р°Р№Р» СЃ failed rules
  local details_file="/reports/openscap/${name}_details.prom"
  {
    echo "# HELP openscap_rule_result OpenSCAP rule results (0=fail, 1=pass)"
    echo "# TYPE openscap_rule_result gauge"

    # РР·РІР»РµС‡СЊ failed rules РЅР°РїСЂСЏРјСѓСЋ РёР· XML
    grep -B 2 '<result>fail</result>' "$xml_file" | grep 'rule-result' | head -30 | while read -r line; do
      # РР·РІР»РµС‡СЊ rule_id
      rule_id=$(echo "$line" | sed -n 's/.*idref="\([^"]*\)".*/\1/p' | sed 's/xccdf_org\.ssgproject\.content_rule_//')
      # РР·РІР»РµС‡СЊ severity
      severity=$(echo "$line" | sed -n 's/.*severity="\([^"]*\)".*/\1/p')

      if [ -n "$rule_id" ] && [ -n "$severity" ]; then
        # РџРѕР»СѓС‡РёС‚СЊ title РґР»СЏ СЌС‚РѕРіРѕ rule (РёСЃРїРѕР»СЊР·СѓРµРј РєРѕСЂРѕС‚РєРёР№ rule_id РєР°Рє title)
        title=$(echo "$rule_id" | sed 's/_/ /g' | cut -c1-60)

        # Р­РєСЂР°РЅРёСЂРѕРІР°С‚СЊ РєР°РІС‹С‡РєРё
        title=${title//\"/}

        echo "openscap_rule_result{host=\"${name}\",rule_id=\"${rule_id}\",severity=\"${severity}\",title=\"${title}\"} 0"
      fi
    done
  } > "$details_file"

  echo "[OpenSCAP] Metrics saved to $metrics_file" >&2
  echo "[OpenSCAP] Details saved to $details_file" >&2
}

status=0

for target in "${targets[@]}"; do
  install_openscap "$target"
  rc=$?
  if [[ $rc -eq 2 ]]; then
    continue
  fi
  if [[ $rc -ne 0 ]]; then
    echo "Failed to install OpenSCAP in $target" >&2
    status=1
    continue
  fi

  if ! scan_container "$target"; then
    status=1
  fi
done

exit $status
