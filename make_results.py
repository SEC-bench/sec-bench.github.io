#!/usr/bin/env python3
"""Create data/results.json only when the checked-in snapshot is absent."""

import copy
import csv
import json
import os
import re
from pathlib import Path

from build import (
    RESULTS_DATA_FILE,
    float_value,
    format_runtime_minutes,
    format_token_count,
    int_value,
    load_yaml_data,
    normalize_run_detail_summary_metrics,
    percent,
    token_count_value,
    token_pair_from_counts,
)


TRAJECTORIES_ENV_VAR = "SEC_BENCH_TRAJECTORIES_DIR"
NO_POC_STATUSES = {"no_js", "no_poc"}
PUBLISH_DATE = "2026-06-17"

RESULT_VERSIONS = (
    {
        "name": "260505",
        "date": "2026-05-05",
        "title": "Initial V8 + SpiderMonkey release",
        "summary": "103 V8 + 80 SpiderMonkey instances",
        "default": False,
    },
    {
        "name": "260617",
        "date": "2026-06-17",
        "title": "Linux + SpiderMonkey extension",
        "summary": "103 V8 + 104 SpiderMonkey + 137 Linux instances",
        "default": True,
    },
)

DEFAULT_RESULT_VERSION = "260617"

SM_260617_ADDED_IDS = {
    "1675905",
    "1736307",
    "1736310",
    "1739972",
    "1838587",
    "1863391",
    "1871618",
    "1875795",
    "1878261",
    "1884518",
    "1895123",
    "1934365",
    "1965751",
    "1970811",
    "1979359",
    "1985224",
    "1985765",
    "1987624",
    "1988967",
    "1994994",
    "2000469",
    "2003589",
    "2023007",
    "2024918",
}

PROJECTS = (
    {
        "source": "v8",
        "name": "v8",
        "display_name": "V8",
        "short_name": "V8",
        "logo": "https://v8.dev/_img/v8.svg",
        "description": "<strong>V8</strong> is Google's open-source JavaScript and WebAssembly engine. This track includes <strong>{instances}</strong> source-file instances.",
    },
    {
        "source": "sm",
        "name": "firefox",
        "display_name": "Firefox",
        "short_name": "Firefox",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Firefox_logo%2C_2019.svg",
        "description": "<strong>Firefox</strong> tracks SpiderMonkey JavaScript and WebAssembly engine vulnerabilities. This track includes <strong>{instances}</strong> source-file instances.",
    },
    {
        "source": "linux",
        "name": "linux",
        "display_name": "Linux",
        "short_name": "Linux",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/3/35/Tux.svg",
        "description": "<strong>Linux</strong> evaluates kernel vulnerability discovery and PoC generation. This track includes <strong>{instances}</strong> source-file instances.",
    },
)

RUNS = (
    {
        "key": "codex_gpt-5.5",
        "agent": "Codex",
        "model": "GPT-5.5",
        "model_version": "GPT-5.5",
        "org": "OpenAI",
        "backend": "OpenAI",
        "effort": "xhigh",
        "open_source": False,
        "slug": "codex_gpt-5.5-xhigh",
    },
    {
        "key": "codex_gpt-5.4",
        "agent": "Codex",
        "model": "GPT-5.4",
        "model_version": "GPT-5.4",
        "org": "OpenAI",
        "backend": "OpenAI",
        "effort": "xhigh",
        "open_source": False,
        "slug": "codex_gpt-5.4-xhigh",
    },
    {
        "key": "claude_opus-4.6",
        "agent": "Claude Code",
        "model": "Opus 4.6",
        "model_version": "Opus 4.6",
        "org": "Anthropic",
        "backend": "AWS Bedrock",
        "effort": "max",
        "open_source": False,
        "slug": "claude_opus-4.6-max",
    },
    {
        "key": "opencode_glm-5",
        "agent": "OpenCode",
        "model": "GLM-5",
        "model_version": "GLM-5",
        "org": "Z.ai",
        "backend": "AWS Bedrock",
        "effort": "high",
        "open_source": True,
        "slug": "opencode_glm-5-high",
    },
    {
        "key": "opencode_kimi-k2.5",
        "agent": "OpenCode",
        "model": "Kimi K2.5",
        "model_version": "Kimi K2.5",
        "org": "Moonshot AI",
        "backend": "AWS Bedrock",
        "effort": "high",
        "open_source": True,
        "slug": "opencode_kimi-k2.5-high",
    },
    {
        "key": "opencode_minimax-m2.5",
        "agent": "OpenCode",
        "model": "MiniMax M2.5",
        "model_version": "MiniMax M2.5",
        "org": "MiniMax",
        "backend": "AWS Bedrock",
        "effort": "high",
        "open_source": True,
        "slug": "opencode_minimax-m2.5-high",
    },
)


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def csv_by_column(path: Path, column: str) -> dict[str, dict]:
    rows = read_csv_rows(path)
    return {str(row.get(column, "")): row for row in rows if row.get(column)}


def format_score_label(solved: int, total: int) -> str:
    return f"{solved}/{total} ({percent(solved, total):.1f}%)" if total else "0/0 (0.0%)"


def read_timeout_info(instance_dir: Path) -> dict:
    path = instance_dir / "timeout"
    if not path.exists():
        return {"timed_out": False, "timeout_secs": None, "exit_code": None}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}

    return {
        "timed_out": bool(data.get("timed_out", True)),
        "timeout_secs": int_value(data.get("timeout_secs"), 0) or None,
        "exit_code": data.get("exit_code"),
    }


def format_duration(seconds) -> str:
    seconds = int_value(seconds, 0)
    if not seconds:
        return ""
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.0f}m"
    hours = minutes / 60
    return f"{hours:.1f}h" if hours % 1 else f"{hours:.0f}h"


def normalize_run_effort(run_meta: dict, effort: str) -> str:
    effort = (effort or "").strip()
    if run_meta.get("key") == "claude_opus-4.6":
        return "max"
    return effort


def read_run_settings(run_dir: Path, run_meta: dict) -> dict:
    settings = {
        "agent": run_meta["agent"],
        "model": run_meta["model"],
        "effort": run_meta.get("effort", ""),
    }

    for child in sorted(p for p in run_dir.iterdir() if p.is_dir()):
        codex_config = child / "config.toml"
        if codex_config.exists():
            raw = codex_config.read_text(encoding="utf-8")
            model = re.search(r'^\s*model\s*=\s*"([^"]+)"', raw, re.MULTILINE)
            effort = re.search(
                r'^\s*model_reasoning_effort\s*=\s*"([^"]+)"',
                raw,
                re.MULTILINE,
            )
            if model:
                settings["model"] = model.group(1)
            if effort:
                settings["effort"] = effort.group(1)
            return settings

        claude_settings = child / "settings.json"
        if claude_settings.exists():
            try:
                data = json.loads(claude_settings.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
            settings["model"] = data.get("model", settings["model"])
            settings["effort"] = data.get("effortLevel", settings["effort"])
            return settings

        opencode_settings = child / "opencode.json"
        if opencode_settings.exists():
            try:
                data = json.loads(opencode_settings.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
            agent = data.get("agent", {}).get("opencode", {})
            settings["model"] = agent.get("model", settings["model"])
            settings["effort"] = agent.get("reasoningEffort", settings["effort"])
            return settings

    return settings


def read_judge_usage(summary_dir: Path) -> dict:
    path = summary_dir / "judge_usage.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def score_mode(solved: int, total: int) -> dict:
    return {
        "solved": solved,
        "total": total,
        "score": percent(solved, total),
        "score_label": format_score_label(solved, total),
    }


def apply_score_ranks(results: list[dict]):
    for mode in ("headline", "completed"):
        ranked = sorted(
            results,
            key=lambda item: item["score_modes"][mode]["score"],
            reverse=True,
        )
        for index, item in enumerate(ranked, 1):
            item["score_modes"][mode]["rank"] = index
            if mode == "headline":
                item["rank"] = index
                item["rank_headline"] = index
            else:
                item["rank_completed"] = index


def instance_result_label(row: dict, timed_out: bool) -> tuple[str, str]:
    if row.get("success") == "yes":
        return "Solved", "At least one candidate PoC was verified against the target criteria."
    if timed_out:
        return "TIMEOUT", "The agent hit the per-instance wall-clock cap before a successful final artifact was verified."
    if row.get("status") in NO_POC_STATUSES:
        return "No PoC", "No candidate PoC file was found for this instance."
    if row.get("status") == "checked":
        return "Checked", "Candidate PoCs were graded, but none satisfied the target criteria."
    return row.get("status", "Unknown").replace("_", " ").title(), row.get("notes", "")


def build_instance_detail(row: dict, run_dir: Path, tokens: dict, tools: dict) -> dict:
    instance_id = str(row.get("instance_id", ""))
    timeout = read_timeout_info(run_dir / instance_id)
    timed_out = timeout["timed_out"]
    result, result_description = instance_result_label(row, timed_out)
    token_row = tokens.get(instance_id, {})
    tool_row = tools.get(instance_id, {})
    runtime_min = float_value(tool_row.get("Runtime_min"))
    tokens_input_count = token_count_value(token_row.get("Input"))
    tokens_output_count = token_count_value(token_row.get("Output"))
    tokens_total_count = token_count_value(token_row.get("Total"))
    if tokens_total_count is None and (
        tokens_input_count is not None or tokens_output_count is not None
    ):
        tokens_total_count = (tokens_input_count or 0) + (tokens_output_count or 0)

    return {
        "id": instance_id,
        "success": row.get("success") == "yes",
        "result": result,
        "result_description": result_description,
        "status": row.get("status", ""),
        "completed": not timed_out,
        "timed_out": timed_out,
        "timeout_secs": timeout.get("timeout_secs"),
        "timeout_label": format_duration(timeout.get("timeout_secs")),
        "expected_type": row.get("expected_type", ""),
        "vulnerability_type": row.get("target_vulnerability_type", ""),
        "poc_total": int_value(row.get("poc_total")),
        "js_total": int_value(row.get("poc_total")),
        "verified_pocs": int_value(row.get("verified_pocs")),
        "unsure_pocs": int_value(row.get("unsure_pocs")),
        "illegal_pocs": int_value(row.get("illegal_pocs")),
        "invalid_pocs": int_value(row.get("invalid_pocs")),
        "runtime_min": runtime_min,
        "runtime_label": token_row.get("Runtime") or (f"{runtime_min:.1f}m" if runtime_min is not None else ""),
        "tool_calls": int_value(tool_row.get("Total")),
        "tokens_total": format_token_count(tokens_total_count),
        "tokens_input": format_token_count(tokens_input_count),
        "tokens_output": format_token_count(tokens_output_count),
        "tokens_total_count": tokens_total_count,
        "tokens_input_count": tokens_input_count,
        "tokens_output_count": tokens_output_count,
        "notes": row.get("notes", ""),
    }


def summarize_run(rows: list[dict], instances: list[dict], judge_usage: dict) -> dict:
    total = len(rows)
    solved = sum(1 for row in rows if row.get("success") == "yes")
    checked = sum(1 for row in rows if row.get("status") == "checked")
    no_poc = sum(1 for row in rows if row.get("status") in NO_POC_STATUSES)
    completed = [item for item in instances if item["completed"]]
    completed_solved = sum(1 for item in completed if item["success"])
    timeouts = sum(1 for item in instances if item["timed_out"])
    timeout_successes = sum(1 for item in instances if item["timed_out"] and item["success"])
    total_runtime = sum(item["runtime_min"] or 0 for item in instances)
    total_tools = sum(item["tool_calls"] or 0 for item in instances)
    total_tokens_input = sum(item.get("tokens_input_count") or 0 for item in instances)
    total_tokens_output = sum(item.get("tokens_output_count") or 0 for item in instances)
    total_tokens = sum(item.get("tokens_total_count") or 0 for item in instances)
    timeout_caps = sorted(
        {item["timeout_secs"] for item in instances if item.get("timeout_secs")}
    )
    usage_cost = (judge_usage.get("cost") or {}).get("total_usd")

    return {
        "instances": total,
        "solved": solved,
        "success_rate": percent(solved, total),
        "checked": checked,
        "no_poc": no_poc,
        "completed_instances": len(completed),
        "completed_solved": completed_solved,
        "completed_rate": percent(completed_solved, len(completed)),
        "timeouts": timeouts,
        "timeout_successes": timeout_successes,
        "timeout_caps": [format_duration(value) for value in timeout_caps],
        "total_runtime_min": round(total_runtime, 1),
        "total_runtime_label": format_runtime_minutes(total_runtime),
        "average_runtime_min": round(total_runtime / total, 1) if total else 0,
        "total_tool_calls": total_tools,
        "average_tool_calls": round(total_tools / total, 1) if total else 0,
        "total_tokens": total_tokens,
        "total_tokens_input": total_tokens_input,
        "total_tokens_output": total_tokens_output,
        "total_tokens_label": token_pair_from_counts(
            total_tokens_input, total_tokens_output
        ),
        "average_tokens": round(total_tokens / total, 1) if total else 0,
        "average_tokens_input": round(total_tokens_input / total, 1) if total else 0,
        "average_tokens_output": round(total_tokens_output / total, 1) if total else 0,
        "average_tokens_label": token_pair_from_counts(
            total_tokens_input / total if total else 0,
            total_tokens_output / total if total else 0,
        ),
        "average_runtime_label": format_runtime_minutes(
            total_runtime / total if total else 0
        ),
        "total_cost": usage_cost,
        "total_calls": total_tools,
        "verified_pocs": sum(int_value(row.get("verified_pocs")) for row in rows),
        "unsure_pocs": sum(int_value(row.get("unsure_pocs")) for row in rows),
        "illegal_pocs": sum(int_value(row.get("illegal_pocs")) for row in rows),
        "invalid_pocs": sum(int_value(row.get("invalid_pocs")) for row in rows),
        "score_modes": {
            "headline": score_mode(solved, total),
            "completed": score_mode(completed_solved, len(completed)),
        },
    }


def build_project_result(project: dict, run_meta: dict, run_dir: Path) -> tuple[dict, dict]:
    summary_dir = run_dir / "summary"
    rows = read_csv_rows(summary_dir / "summary.csv")
    tokens = csv_by_column(summary_dir / "tokens.csv", "Instance")
    tools = csv_by_column(summary_dir / "tools.csv", "Instance")
    judge_usage = read_judge_usage(summary_dir)
    instances = [
        build_instance_detail(row, run_dir, tokens, tools)
        for row in rows
    ]
    summary = summarize_run(rows, instances, judge_usage)
    settings = read_run_settings(run_dir, run_meta)
    display_effort = normalize_run_effort(
        run_meta,
        settings.get("effort") or run_meta.get("effort", ""),
    )
    settings = dict(settings)
    settings["effort"] = display_effort

    result = {
        "agent": run_meta["agent"],
        "model": run_meta["model"],
        "model_version": run_meta["model_version"],
        "effort": display_effort,
        "org": run_meta["org"],
        "backend": run_meta["backend"],
        "resolved": summary["score_modes"]["headline"]["score"],
        "date": PUBLISH_DATE,
        "open_source": run_meta["open_source"],
        "verified": False,
        "logs_link": "",
        "details": {
            "slug": run_meta["slug"],
            "source_run": f"{project['source']}/{run_dir.name}",
        },
        "score_modes": summary["score_modes"],
        "completed_instances": summary["completed_instances"],
        "timeouts": summary["timeouts"],
        "footnote": "Use the score filter to compare headline scores with completed-only runs.",
    }

    detail = {
        "target": project["name"],
        "target_display_name": project["display_name"],
        "project": project["source"],
        "slug": run_meta["slug"],
        "agent": run_meta["agent"],
        "model": run_meta["model"],
        "model_version": run_meta["model_version"],
        "effort": display_effort,
        "org": run_meta["org"],
        "backend": run_meta["backend"],
        "date": PUBLISH_DATE,
        "source_run": f"{project['source']}/{run_dir.name}",
        "settings": settings,
        "summary": summary,
        "instances": instances,
    }

    return result, detail


def build_overall_result(run_meta: dict, project_results: dict) -> dict:
    project_parts = []
    headline_total = 0
    headline_solved = 0
    completed_total = 0
    completed_solved = 0
    timeouts = 0

    for project in PROJECTS:
        result = project_results[project["name"]][run_meta["key"]]
        headline = result["score_modes"]["headline"]
        completed = result["score_modes"]["completed"]
        headline_total += headline["total"]
        headline_solved += headline["solved"]
        completed_total += completed["total"]
        completed_solved += completed["solved"]
        timeouts += result["timeouts"]
        project_parts.append(
            {
                "name": project["name"],
                "label": project["short_name"],
                "solved": headline["solved"],
                "total": headline["total"],
                "score": headline["score"],
                "score_modes": {
                    "headline": dict(headline),
                    "completed": dict(completed),
                },
            }
        )

    for part in project_parts:
        part["score_modes"]["headline"]["width"] = percent(
            part["score_modes"]["headline"]["solved"],
            headline_total,
        )
        part["score_modes"]["completed"]["width"] = percent(
            part["score_modes"]["completed"]["solved"],
            completed_total,
        )

    return {
        "agent": run_meta["agent"],
        "model": run_meta["model"],
        "model_version": run_meta["model_version"],
        "effort": normalize_run_effort(run_meta, run_meta.get("effort", "")),
        "org": run_meta["org"],
        "backend": run_meta["backend"],
        "resolved": percent(headline_solved, headline_total),
        "date": PUBLISH_DATE,
        "open_source": run_meta["open_source"],
        "verified": False,
        "score_modes": {
            "headline": score_mode(headline_solved, headline_total),
            "completed": score_mode(completed_solved, completed_total),
        },
        "completed_instances": completed_total,
        "timeouts": timeouts,
        "projects": project_parts,
    }


def load_trajectory_data(trajectories_dir: Path, site_config: dict) -> dict:
    info_sections = site_config.get("pro_common_info_sections", [])
    run_by_key = {run["key"]: run for run in RUNS}
    project_results = {project["name"]: {} for project in PROJECTS}
    run_details = {}
    leaderboards = []

    for project in PROJECTS:
        results = []
        for run_meta in RUNS:
            run_dir = trajectories_dir / project["source"] / f"{run_meta['key']}_source-files"
            summary_csv = run_dir / "summary" / "summary.csv"
            if not summary_csv.exists():
                raise SystemExit(f"Missing trajectory summary: {summary_csv}")
            result, detail = build_project_result(project, run_meta, run_dir)
            results.append(result)
            project_results[project["name"]][run_meta["key"]] = result
            run_details[(project["name"], run_meta["slug"])] = detail

        apply_score_ranks(results)
        total_instances = results[0]["score_modes"]["headline"]["total"] if results else 0
        leaderboards.append(
            {
                "name": project["name"],
                "display_name": project["display_name"],
                "description": f"{project['display_name']} source-file leaderboard.",
                "instances": total_instances,
                "results": results,
                "info_sections": info_sections,
            }
        )

    overall_results = [
        build_overall_result(run_by_key[run["key"]], project_results)
        for run in RUNS
        if all(run["key"] in project_results[project["name"]] for project in PROJECTS)
    ]
    apply_score_ranks(overall_results)
    overall_total = sum(
        leaderboard["results"][0]["score_modes"]["headline"]["total"]
        for leaderboard in leaderboards
        if leaderboard["results"]
    )

    leaderboards.insert(
        0,
        {
            "name": "overall",
            "display_name": "Overall",
            "description": "Overall performance across V8, Firefox, and Linux.",
            "instances": overall_total,
            "is_overall": True,
            "results": overall_results,
            "info_sections": info_sections,
        },
    )

    target_tabs = [
        {
            "name": "overall",
            "display_name": "Overall",
            "leaderboard": "overall",
            "status": "available",
            "description": f"<strong>Overall</strong> aggregates V8, Firefox, and Linux into a <strong>{overall_total}</strong>-instance leaderboard. Split bars show how each project contributes to the score.",
        }
    ]
    for project in PROJECTS:
        instances = next(
            (
                board["instances"]
                for board in leaderboards
                if board["name"] == project["name"]
            ),
            0,
        )
        target_tabs.append(
            {
                "name": project["name"],
                "display_name": project["display_name"],
                "logo": project["logo"],
                "leaderboard": project["name"],
                "instances": instances,
                "status": "available",
                "description": project["description"].format(instances=instances),
            }
        )

    return {
        "leaderboards": leaderboards,
        "target_tabs": target_tabs,
        "run_details": run_details,
    }


def serialize_results_data(generated: dict) -> dict:
    leaderboards = [
        {key: value for key, value in leaderboard.items() if key != "info_sections"}
        for leaderboard in generated.get("leaderboards", [])
    ]
    details = {
        f"{target}/{slug}": detail
        for (target, slug), detail in sorted(generated.get("run_details", {}).items())
    }
    return {
        "leaderboards": leaderboards,
        "target_tabs": generated.get("target_tabs", []),
        "run_details": details,
    }


def result_key(result: dict) -> tuple:
    return (
        result.get("agent"),
        result.get("model"),
        result.get("effort"),
        result.get("org"),
    )


def result_slug(result: dict) -> str | None:
    details = result.get("details") if isinstance(result.get("details"), dict) else {}
    return details.get("slug") if details else None


def summarize_instances(instances: list[dict], original_summary: dict | None = None) -> dict:
    total = len(instances)
    solved = sum(1 for instance in instances if instance.get("success"))
    checked = sum(1 for instance in instances if instance.get("status") == "checked")
    no_poc = sum(
        1 for instance in instances if instance.get("status") in NO_POC_STATUSES
    )
    completed = [instance for instance in instances if instance.get("completed")]
    completed_solved = sum(1 for instance in completed if instance.get("success"))
    timeouts = sum(1 for instance in instances if instance.get("timed_out"))
    timeout_successes = sum(
        1
        for instance in instances
        if instance.get("timed_out") and instance.get("success")
    )
    timeout_caps = sorted(
        {instance.get("timeout_label") for instance in instances if instance.get("timeout_label")}
    )
    total_runtime = sum(instance.get("runtime_min") or 0 for instance in instances)
    total_tools = sum(instance.get("tool_calls") or 0 for instance in instances)
    total_tokens_input = sum(
        instance.get("tokens_input_count") or 0 for instance in instances
    )
    total_tokens_output = sum(
        instance.get("tokens_output_count") or 0 for instance in instances
    )
    total_tokens = sum(instance.get("tokens_total_count") or 0 for instance in instances)
    if not total_tokens and (total_tokens_input or total_tokens_output):
        total_tokens = total_tokens_input + total_tokens_output

    return {
        "instances": total,
        "solved": solved,
        "success_rate": percent(solved, total),
        "checked": checked,
        "no_poc": no_poc,
        "completed_instances": len(completed),
        "completed_solved": completed_solved,
        "completed_rate": percent(completed_solved, len(completed)),
        "timeouts": timeouts,
        "timeout_successes": timeout_successes,
        "timeout_caps": timeout_caps,
        "total_runtime_min": round(total_runtime, 1),
        "total_runtime_label": format_runtime_minutes(total_runtime),
        "average_runtime_min": round(total_runtime / total, 1) if total else 0,
        "total_tool_calls": total_tools,
        "average_tool_calls": round(total_tools / total, 1) if total else 0,
        "total_tokens": total_tokens,
        "total_tokens_input": total_tokens_input,
        "total_tokens_output": total_tokens_output,
        "total_tokens_label": token_pair_from_counts(
            total_tokens_input, total_tokens_output
        ),
        "average_tokens": round(total_tokens / total, 1) if total else 0,
        "average_tokens_input": round(total_tokens_input / total, 1) if total else 0,
        "average_tokens_output": round(total_tokens_output / total, 1) if total else 0,
        "average_tokens_label": token_pair_from_counts(
            total_tokens_input / total if total else 0,
            total_tokens_output / total if total else 0,
        ),
        "average_runtime_label": format_runtime_minutes(
            total_runtime / total if total else 0
        ),
        "total_cost": (original_summary or {}).get("total_cost"),
        "total_calls": total_tools,
        "verified_pocs": sum(instance.get("verified_pocs") or 0 for instance in instances),
        "unsure_pocs": sum(instance.get("unsure_pocs") or 0 for instance in instances),
        "illegal_pocs": sum(instance.get("illegal_pocs") or 0 for instance in instances),
        "invalid_pocs": sum(instance.get("invalid_pocs") or 0 for instance in instances),
        "score_modes": {
            "headline": score_mode(solved, total),
            "completed": score_mode(completed_solved, len(completed)),
        },
    }


def update_snapshot_detail_ranks(snapshot: dict, leaderboard: dict):
    target = leaderboard["name"]
    if target == "overall":
        return

    for result in leaderboard.get("results", []):
        slug = result_slug(result)
        detail = snapshot["run_details"].get(f"{target}/{slug}") if slug else None
        if not detail:
            continue
        for mode in ("headline", "completed"):
            detail["summary"]["score_modes"][mode]["rank"] = result["score_modes"][mode]["rank"]


def build_snapshot_project_board(
    snapshot: dict,
    source_snapshot: dict,
    target: str,
    keep_ids: set[str] | None = None,
) -> dict:
    source_board = next(
        board for board in source_snapshot["leaderboards"] if board["name"] == target
    )
    board = copy.deepcopy(source_board)
    results = []

    for result in board["results"]:
        slug = result_slug(result)
        detail_key = f"{target}/{slug}"
        detail = copy.deepcopy(source_snapshot["run_details"][detail_key])
        if keep_ids is not None:
            detail["instances"] = [
                instance
                for instance in detail["instances"]
                if str(instance.get("id")) in keep_ids
            ]
        detail["summary"] = summarize_instances(
            detail["instances"], detail.get("summary", {})
        )
        snapshot["run_details"][detail_key] = detail

        updated = copy.deepcopy(result)
        summary = detail["summary"]
        updated["resolved"] = summary["score_modes"]["headline"]["score"]
        updated["score_modes"] = copy.deepcopy(summary["score_modes"])
        updated["completed_instances"] = summary["completed_instances"]
        updated["timeouts"] = summary["timeouts"]
        results.append(updated)

    board["results"] = results
    board["instances"] = results[0]["score_modes"]["headline"]["total"] if results else 0
    apply_score_ranks(board["results"])
    update_snapshot_detail_ranks(snapshot, board)
    return board


def build_snapshot_overall_board(
    source_snapshot: dict,
    project_boards: list[dict],
) -> dict:
    source_overall = next(
        board for board in source_snapshot["leaderboards"] if board["name"] == "overall"
    )
    board = copy.deepcopy(source_overall)
    board["instances"] = sum(project["instances"] for project in project_boards)
    board["description"] = "Overall performance across V8 and Firefox."
    board["results"] = []
    project_by_name = {project["name"]: project for project in project_boards}

    for source_result in source_overall["results"]:
        key = result_key(source_result)
        project_parts = []
        headline_total = 0
        headline_solved = 0
        completed_total = 0
        completed_solved = 0
        timeouts = 0

        for project_name, label in (("v8", "V8"), ("firefox", "Firefox")):
            project_result = next(
                result
                for result in project_by_name[project_name]["results"]
                if result_key(result) == key
            )
            headline = project_result["score_modes"]["headline"]
            completed = project_result["score_modes"]["completed"]
            headline_total += headline["total"]
            headline_solved += headline["solved"]
            completed_total += completed["total"]
            completed_solved += completed["solved"]
            timeouts += project_result.get("timeouts", 0)
            project_parts.append(
                {
                    "name": project_name,
                    "label": label,
                    "solved": headline["solved"],
                    "total": headline["total"],
                    "score": headline["score"],
                    "score_modes": {
                        "headline": copy.deepcopy(headline),
                        "completed": copy.deepcopy(completed),
                    },
                }
            )

        for part in project_parts:
            part["score_modes"]["headline"]["width"] = percent(
                part["score_modes"]["headline"]["solved"], headline_total
            )
            part["score_modes"]["completed"]["width"] = percent(
                part["score_modes"]["completed"]["solved"], completed_total
            )

        updated = copy.deepcopy(source_result)
        for key_to_remove in ("details", "details_available", "details_url", "details_summary"):
            updated.pop(key_to_remove, None)
        updated["resolved"] = percent(headline_solved, headline_total)
        updated["score_modes"] = {
            "headline": score_mode(headline_solved, headline_total),
            "completed": score_mode(completed_solved, completed_total),
        }
        updated["completed_instances"] = completed_total
        updated["timeouts"] = timeouts
        updated["projects"] = project_parts
        board["results"].append(updated)

    apply_score_ranks(board["results"])
    return board


def build_snapshot_target_tabs(source_snapshot: dict, project_boards: list[dict]) -> list[dict]:
    totals = {board["name"]: board["instances"] for board in project_boards}
    overall_total = sum(totals.values())
    current_tabs = {tab["name"]: copy.deepcopy(tab) for tab in source_snapshot["target_tabs"]}
    tabs = [
        {
            "name": "overall",
            "display_name": "Overall",
            "leaderboard": "overall",
            "instances": overall_total,
            "status": "available",
            "description": f"<strong>Overall</strong> aggregates V8 and Firefox into a <strong>{overall_total}</strong>-instance leaderboard. Split bars show how each project contributes to the score.",
        }
    ]

    for target_name, instances in (("v8", 103), ("firefox", 80)):
        tab = current_tabs[target_name]
        tab["instances"] = totals[target_name]
        if target_name == "v8":
            tab["description"] = f"<strong>V8</strong> is Google's open-source JavaScript and WebAssembly engine that powers Chrome and Node.js. This snapshot includes <strong>{instances}</strong> instances."
        else:
            tab["description"] = f"<strong>Firefox</strong> tracks SpiderMonkey JavaScript and WebAssembly engine vulnerabilities. This snapshot includes <strong>{instances}</strong> instances."
        tabs.append(tab)

    return tabs


def build_260505_snapshot(source_snapshot: dict) -> dict:
    firefox_ids = {
        str(instance["id"])
        for detail_key, detail in source_snapshot["run_details"].items()
        if detail_key.startswith("firefox/")
        for instance in detail.get("instances", [])
    }
    initial_firefox_ids = firefox_ids - SM_260617_ADDED_IDS
    if len(initial_firefox_ids) != 80:
        raise SystemExit(
            f"Expected 80 initial SpiderMonkey instances, got {len(initial_firefox_ids)}"
        )

    snapshot = {"leaderboards": [], "target_tabs": [], "run_details": {}}
    v8_board = build_snapshot_project_board(snapshot, source_snapshot, "v8")
    firefox_board = build_snapshot_project_board(
        snapshot, source_snapshot, "firefox", initial_firefox_ids
    )
    overall_board = build_snapshot_overall_board(
        source_snapshot, [v8_board, firefox_board]
    )
    snapshot["leaderboards"] = [overall_board, v8_board, firefox_board]
    snapshot["target_tabs"] = build_snapshot_target_tabs(
        source_snapshot, [v8_board, firefox_board]
    )
    return snapshot


def build_versioned_results_data(current_snapshot: dict) -> dict:
    return {
        "versions": list(RESULT_VERSIONS),
        "default_version": DEFAULT_RESULT_VERSION,
        "snapshots": {
            "260505": build_260505_snapshot(current_snapshot),
            "260617": current_snapshot,
        },
    }


def write_results_data(data_dir: Path, generated: dict):
    path = data_dir / RESULTS_DATA_FILE
    snapshot = build_versioned_results_data(serialize_results_data(generated))
    path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def make_results_file(base_dir: Path) -> Path:
    data_dir = base_dir / "data"
    results_path = data_dir / RESULTS_DATA_FILE
    if results_path.exists():
        print(f"✓ Using existing {results_path.relative_to(base_dir)}")
        return results_path

    raw_trajectories_dir = os.environ.get(TRAJECTORIES_ENV_VAR)
    if not raw_trajectories_dir:
        raise SystemExit(
            f"{results_path.relative_to(base_dir)} is missing. "
            f"Set {TRAJECTORIES_ENV_VAR}=/path/to/trajectories and rerun make build."
        )

    trajectories_dir = Path(raw_trajectories_dir).expanduser()
    if not trajectories_dir.exists():
        raise SystemExit(
            f"{TRAJECTORIES_ENV_VAR} points to a missing directory: {trajectories_dir}"
        )

    leaderboards_data = load_yaml_data(data_dir / "leaderboards.yaml")
    generated = load_trajectory_data(trajectories_dir, leaderboards_data)
    normalize_run_detail_summary_metrics(generated["run_details"])
    write_results_data(data_dir, generated)
    print(f"✓ Generated {results_path.relative_to(base_dir)} from {trajectories_dir}")
    return results_path


def main():
    make_results_file(Path(__file__).parent)


if __name__ == "__main__":
    main()
