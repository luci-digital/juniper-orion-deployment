#!/bin/bash
# R730 ORION Health Hook for Claude Code Sessions
# Source this in sessionstart.sh
# Genesis Bond: ACTIVE @ 741 Hz

check_r730_orion() {
    local R730_IP="${R730_DATA_IP:-192.168.1.141}"
    local HEALTH_PORT="${R730_HEALTH_PORT:-9200}"

    # Quick connectivity test
    if ! ping -c 1 -W 1 "$R730_IP" >/dev/null 2>&1; then
        echo "✗ R730 ORION: OFFLINE (no ping)"
        return 1
    fi

    # Health endpoint test
    local health_data=$(curl -sf --connect-timeout 2 "http://${R730_IP}:${HEALTH_PORT}/health" 2>/dev/null)

    if [ -z "$health_data" ]; then
        echo "⚠ R730 ORION: UP but health monitor not responding"
        return 1
    fi

    # Parse WAN status
    local healthy_wans=$(echo "$health_data" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    healthy = [k for k,v in data.items() if v.get('healthy', False)]
    print(','.join(healthy) if healthy else 'NONE')
except:
    print('ERROR')
" 2>/dev/null)

    local wan_count=$(echo "$health_data" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    healthy = sum(1 for v in data.values() if v.get('healthy', False))
    total = len(data)
    print(f'{healthy}/{total}')
except:
    print('?/?')
" 2>/dev/null)

    echo "✓ R730 ORION: HEALTHY (WANs: $wan_count - $healthy_wans)"
    return 0
}

# Get BGP status if birdc is available
check_r730_bgp() {
    local R730_IP="${R730_DATA_IP:-192.168.1.141}"

    # Try SSH to check BGP (requires passwordless SSH)
    local bgp_status=$(ssh -o ConnectTimeout=2 -o BatchMode=yes "root@${R730_IP}" \
        "birdc show protocols | grep -E 'BGP.*Established' | wc -l" 2>/dev/null)

    if [ -n "$bgp_status" ] && [ "$bgp_status" -gt 0 ]; then
        echo "  BGP: $bgp_status sessions established"
    fi
}

# Export for use in sessionstart.sh
export -f check_r730_orion
export -f check_r730_bgp

# If sourced directly, run check
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    check_r730_orion
    check_r730_bgp
fi
