"""
Explainable AI (XAI) & Factor Attribution Module for CricNova.
Translates mathematical model coefficients, feature importances, and match state differentials
into human-readable tactical narratives and analytical insights.
"""

from typing import Dict, List, Any


def explain_pre_match_prediction(
    team1: str,
    team2: str,
    venue: str,
    toss_winner: str,
    toss_decision: str,
    win_prob_team1: float,
    metrics: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Generates structured narrative drivers explaining why the pre-match model
    favors one team over the other.
    """
    explanations = []
    favored_team = team1 if win_prob_team1 >= 0.5 else team2
    margin = abs(win_prob_team1 - (1.0 - win_prob_team1)) * 100

    # 1. Recent Form Factor
    t1_form = metrics.get("t1_form5", metrics.get("team1_form_last5", 0.5))
    t2_form = metrics.get("t2_form5", metrics.get("team2_form_last5", 0.5))
    form_diff = t1_form - t2_form
    
    if abs(form_diff) >= 0.15:
        better_team = team1 if form_diff > 0 else team2
        worse_team = team2 if form_diff > 0 else team1
        high_form = max(t1_form, t2_form) * 100
        low_form = min(t1_form, t2_form) * 100
        explanations.append({
            "category": "Recent Momentum & Form",
            "impact": "High Positive" if better_team == favored_team else "Contrarian Risk",
            "icon": "🔥",
            "narrative": (
                f"{better_team} carries stronger recent form into this encounter, winning "
                f"{high_form:.0f}% of their last 5 matches compared to {worse_team}'s {low_form:.0f}%."
            )
        })
    else:
        explanations.append({
            "category": "Recent Momentum & Form",
            "impact": "Neutral",
            "icon": "⚖️",
            "narrative": (
                f"Both squads possess balanced recent form over their last 5 fixtures "
                f"({t1_form*100:.0f}% vs {t2_form*100:.0f}% win rate)."
            )
        })

    # 2. Head-to-Head Record
    h2h_batting = metrics.get("t1_h2h_win_pct", metrics.get("h2h_win_rate_batting", 0.5))
    if abs(h2h_batting - 0.5) >= 0.08:
        leader = team1 if h2h_batting > 0.5 else team2
        rate = max(h2h_batting, 1.0 - h2h_batting) * 100
        explanations.append({
            "category": "Historical Head-to-Head",
            "impact": "Moderate Positive" if leader == favored_team else "Historical Drag",
            "icon": "⚔️",
            "narrative": (
                f"Historical matchups tilt toward {leader}, who holds a {rate:.1f}% win rate "
                f"across past IPL head-to-head encounters."
            )
        })
    else:
        explanations.append({
            "category": "Head-to-Head Equilibrium",
            "impact": "Neutral / Balanced Prior",
            "icon": "⚔️",
            "narrative": (
                f"Head-to-head records show even balance (or no previous era meetings); "
                f"ML model evaluates prediction based on overall franchise strength and venue par."
            )
        })

    # 3. Ground & Venue Advantage
    t1_venue = metrics.get("venue_chase_win_pct", metrics.get("team1_venue_win_rate", 0.5))
    avg_1st = metrics.get("venue_avg_1st_inns", metrics.get("venue_avg_1st_innings", 165))
    explanations.append({
        "category": "Venue Characteristics",
        "impact": "Tactical Factor",
        "icon": "🏟️",
        "narrative": (
            f"At {venue}, historical chasing teams win {t1_venue*100:.1f}% of fixtures. "
            f"Average first-innings score is {avg_1st:.0f} runs."
        )
    })

    # 4. Toss & Match Tactics
    toss_winner_name = team1 if toss_winner == team1 else team2
    explanations.append({
        "category": "Toss & Match Tactics",
        "impact": "Tactical Edge",
        "icon": "🪙",
        "narrative": (
            f"{toss_winner_name} opted to {toss_decision}. Historical 1st innings par score at "
            f"{venue} is {avg_1st:.0f} runs, with pitch dynamics heavily influencing dew factor."
        )
    })

    return explanations


def explain_live_chase_prediction(
    batting_team: str,
    bowling_team: str,
    target: int,
    current_score: int,
    balls_remaining: int,
    wickets_in_hand: int,
    crr: float,
    rrr: float,
    win_prob_batting: float,
    runs_last_5: int,
    wickets_last_5: int
) -> List[Dict[str, str]]:
    """
    Explains the real-time Win Probability calculation during the 2nd innings chase.
    """
    explanations = []
    runs_required = target - current_score
    rr_diff = crr - rrr

    # 1. Run Rate Equation
    if rrr <= 7.0:
        explanations.append({
            "category": "Run Rate Dynamic",
            "impact": "Heavy Advantage",
            "icon": "📈",
            "narrative": (
                f"Controlled Equation: Required Run Rate is a manageable {rrr:.2f} RPO. "
                f"Batting side needs only {runs_required} runs from {balls_remaining} deliveries."
            )
        })
    elif rrr <= 10.0:
        impact = "Par Equation" if rr_diff >= 0 else "Escalating Pressure"
        explanations.append({
            "category": "Run Rate Dynamic",
            "impact": impact,
            "icon": "⚖️",
            "narrative": (
                f"Contested Chase: Current Run Rate ({crr:.2f} RPO) vs Required Rate ({rrr:.2f} RPO). "
                f"{'Batters are keeping pace with the target' if rr_diff >= 0 else 'The required rate is climbing steadily above current scoring' }."
            )
        })
    else:
        explanations.append({
            "category": "Run Rate Dynamic",
            "impact": "Severe Pressure",
            "icon": "🚨",
            "narrative": (
                f"Steep Climbing RRR: At {rrr:.2f} RPO, the chasing team must execute high-risk boundary hitting "
                f"to achieve {runs_required} off the remaining {balls_remaining} balls."
            )
        })

    # 2. Resource Cushion (Wickets in Hand)
    if wickets_in_hand >= 7:
        explanations.append({
            "category": "Wicket Resources",
            "impact": "Deep Batting Lineup",
            "icon": "🛡️",
            "narrative": (
                f"High Resource Cushion: With {wickets_in_hand} wickets intact, {batting_team} can absorb "
                f"a few dot balls and launch calculated death overs acceleration."
            )
        })
    elif wickets_in_hand <= 3:
        explanations.append({
            "category": "Wicket Resources",
            "impact": "Tail Exposed",
            "icon": "⚠️",
            "narrative": (
                f"Fragile Situation: Only {wickets_in_hand} wickets remain. A single breakthrough will severely "
                f"diminish victory probability as lower-order batters arrive."
            )
        })
    else:
        explanations.append({
            "category": "Wicket Resources",
            "impact": "Balanced Depth",
            "icon": "🏏",
            "narrative": (
                f"Moderate Wicket Capital: {wickets_in_hand} wickets in hand requires top-order anchors to bat deep."
            )
        })

    # 3. Recent Phase Momentum (Last 5 Overs)
    if runs_last_5 >= 45:
        explanations.append({
            "category": "Phase Momentum",
            "impact": "Surging Momentum",
            "icon": "⚡",
            "narrative": (
                f"Recent Surge: Chasing unit accumulated {runs_last_5} runs in the last 5 overs "
                f"({runs_last_5/5:.1f} RPO) for the loss of {wickets_last_5} wicket(s), wresting momentum."
            )
        })
    elif wickets_last_5 >= 3:
        explanations.append({
            "category": "Bowling Impact",
            "impact": "Cluster Wickets",
            "icon": "🎯",
            "narrative": (
                f"Bowling Counter-Punch: {bowling_team} claimed {wickets_last_5} wickets in the last 5 overs, "
                f"stifling the chase and forcing rebuilding."
            )
        })

    return explanations


def explain_score_prediction(
    predicted_score: int,
    lower_bound: int,
    upper_bound: int,
    current_score: int,
    overs_bowled: float,
    wickets_fallen: int,
    crr: float,
    venue_avg: float
) -> List[Dict[str, str]]:
    """
    Explains the 1st innings total projection and uncertainty interval.
    """
    explanations = []
    wickets_in_hand = 10 - wickets_fallen
    remaining_overs = 20.0 - overs_bowled

    # 1. Projected Trajectory
    simple_extrapolation = int(current_score + crr * remaining_overs)
    diff = predicted_score - simple_extrapolation

    if diff > 5:
        explanations.append({
            "category": "Death Overs Boost",
            "impact": "Above Linear Run Rate",
            "icon": "🚀",
            "narrative": (
                f"Model anticipates an accelerated finish (+{diff} runs above current linear pace of {simple_extrapolation}) "
                f"leveraging {wickets_in_hand} wickets in hand and death-over hitting tendencies."
            )
        })
    elif diff < -5:
        explanations.append({
            "category": "Wicket Friction",
            "impact": "Discounted Projection",
            "icon": "📉",
            "narrative": (
                f"Model discounts linear pace by {abs(diff)} runs because {wickets_fallen} wickets have fallen, "
                f"forcing consolidation rather than uninhibited hitting."
            )
        })
    else:
        explanations.append({
            "category": "Pace Consistency",
            "impact": "Steady Trajectory",
            "icon": "📊",
            "narrative": (
                f"Current scoring rate ({crr:.2f} RPO) closely mirrors expected innings trajectory toward ~{predicted_score}."
            )
        })

    # 2. Confidence Interval
    spread = upper_bound - lower_bound
    explanations.append({
        "category": "Scenario Variance",
        "impact": "Range Definition",
        "icon": "🎯",
        "narrative": (
            f"Prediction 80% confidence corridor spans {lower_bound} to {upper_bound} (±{spread//2} runs). "
            f"Upper band represents unbroken partnerships through the death overs; lower band models rapid late-order collapse."
        )
    })

    # 3. Ground Par Comparison
    par_diff = predicted_score - venue_avg
    if abs(par_diff) >= 8:
        status = "Above Par Total" if par_diff > 0 else "Below Par Total"
        explanations.append({
            "category": "Venue Benchmark",
            "impact": status,
            "icon": "🏟️",
            "narrative": (
                f"Projected {predicted_score} is {abs(par_diff):.0f} runs {'higher' if par_diff > 0 else 'lower'} "
                f"than the historical ground par average of {venue_avg:.0f} runs at this venue."
            )
        })

    return explanations
