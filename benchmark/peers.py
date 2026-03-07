"""
Synthetic peer department database for benchmarking.

Generates ~600 realistic US fire departments based on NFPA national
statistics, used when real NERIS aggregate data is unavailable.
"""

import random

STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
]

STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
    "CO":"Colorado","CT":"Connecticut","DE":"Delaware","FL":"Florida","GA":"Georgia",
    "HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa",
    "KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland",
    "MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi",
    "MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire",
    "NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina",
    "ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania",
    "RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee",
    "TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington",
    "WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
}

REGIONS = {
    "Northeast": ["CT","DE","ME","MD","MA","NH","NJ","NY","PA","RI","VT"],
    "Southeast": ["AL","AR","FL","GA","KY","LA","MS","NC","SC","TN","VA","WV"],
    "Midwest":   ["IL","IN","IA","KS","MI","MN","MO","NE","ND","OH","SD","WI"],
    "Southwest": ["AZ","NM","OK","TX"],
    "West":      ["AK","CA","CO","HI","ID","MT","NV","OR","UT","WA","WY"],
}


def get_region(state: str) -> str:
    for region, states in REGIONS.items():
        if state in states:
            return region
    return "Other"


def _generate(seed: int = 42, n: int = 600) -> list[dict]:
    rng = random.Random(seed)
    peers = []

    for _ in range(n):
        state = rng.choice(STATES)
        dept_type = rng.choices(
            ["volunteer", "combination", "career"],
            weights=[65, 25, 10],
        )[0]

        # Population served — log-normal so small depts dominate
        if dept_type == "volunteer":
            pop = max(300, min(int(rng.lognormvariate(8.5, 0.8)), 60_000))
        elif dept_type == "combination":
            pop = max(5_000, min(int(rng.lognormvariate(10.0, 0.7)), 300_000))
        else:
            pop = max(20_000, min(int(rng.lognormvariate(11.5, 0.8)), 1_500_000))

        # Call volume (~80-150 calls per 1,000 pop, mostly EMS-driven)
        rate_per_1000 = rng.uniform(80, 150)
        total_incidents = max(50, int(pop * rate_per_1000 / 1000))

        # Response time — career depts faster; wide spread within types
        base = {"volunteer": 540, "combination": 420, "career": 300}[dept_type]
        avg_rt = max(90, min(rng.gauss(base, 90), 1_080))

        # Incident mix
        ems_pct           = rng.uniform(45, 72)
        fire_pct          = rng.uniform(2, 9)
        structure_pct     = fire_pct * rng.uniform(0.25, 0.65)
        false_alarm_pct   = rng.uniform(8, 22)

        peers.append({
            "state":                state,
            "region":               get_region(state),
            "dept_type":            dept_type,
            "population_served":    pop,
            "total_incidents":      total_incidents,
            "incidents_per_1000":   round(rate_per_1000, 1),
            "avg_response_seconds": round(avg_rt, 1),
            "ems_pct":              round(ems_pct, 1),
            "fire_pct":             round(fire_pct, 1),
            "structure_fire_pct":   round(structure_pct, 1),
            "false_alarm_pct":      round(false_alarm_pct, 1),
        })

    return peers


# Pre-built once at import; deterministic with fixed seed
PEER_DATABASE = _generate()
