from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import streamlit as st

CATEGORY_ICON = "📄"
DEFAULT_CATEGORIES = [
    {"id": "1", "name": "업무", "color": "#4E79A7"},
    {"id": "2", "name": "개인", "color": "#F28E2B"},
    {"id": "3", "name": "공부", "color": "#59A14F"},
]


def init_state() -> None:
    if "categories" not in st.session_state:
        st.session_state.categories = {c["id"]: c for c in DEFAULT_CATEGORIES}
        st.session_state.next_category_id = 4

    if "tasks" not in st.session_state:
        st.session_state.tasks = []
        st.session_state.next_task_id = 1


def add_category(name: str, color: str) -> None:
    category_id = str(st.session_state.next_category_id)
    st.session_state.categories[category_id] = {
        "id": category_id,
        "name": name,
        "color": color,
    }
    st.session_state.next_category_id += 1


def submit_new_task() -> None:
    title = st.session_state.task_title
    category_id = st.session_state.task_category
    note = st.session_state.task_note

    if not title.strip():
        st.warning("작업 제목을 입력해주세요.")
        return

    st.session_state.tasks.append(
        {
            "id": str(st.session_state.next_task_id),
            "title": title.strip(),
            "category_id": category_id,
            "note": note.strip(),
            "status": "할 일",
            "start_time": None,
            "end_time": None,
            "created_at": datetime.now(),
        }
    )
    st.session_state.next_task_id += 1
    st.session_state.task_title = ""
    st.session_state.task_note = ""
    st.toast("할 일이 추가되었습니다.", icon="✅")


def start_task(task_id: str, start_time: datetime) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["status"] = "진행 중"
            task["start_time"] = start_time
            task["end_time"] = None
            break


def complete_task(task_id: str, end_time: datetime) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["status"] = "완료"
            task["end_time"] = end_time
            if not task["start_time"]:
                task["start_time"] = end_time
            break


def delete_task(task_id: str) -> None:
    st.session_state.tasks = [task for task in st.session_state.tasks if task["id"] != task_id]


def delete_category(category_id: str) -> None:
    if category_id in st.session_state.categories:
        del st.session_state.categories[category_id]
        st.session_state.tasks = [
            task for task in st.session_state.tasks if task["category_id"] != category_id
        ]


def render_category_badge(category_id: str) -> str:
    category = st.session_state.categories.get(category_id)
    if not category:
        return "미분류"
    return f"<span style='background:{category['color']};color:#fff;padding:4px 8px;border-radius:12px;font-weight:600;'>{CATEGORY_ICON} {category['name']}</span>"


def render_task_card(task: dict[str, Any]) -> None:
    category = st.session_state.categories.get(task["category_id"], {})
    card_color = category.get("color", "#999999")

    start_text = task["start_time"].strftime("%Y-%m-%d %H:%M") if task["start_time"] else "미정"
    end_text = task["end_time"].strftime("%Y-%m-%d %H:%M") if task["end_time"] else "미정"

    st.markdown(
        f"<div style='border:1px solid #ddd;border-left:6px solid {card_color};border-radius:12px;padding:16px;margin-bottom:12px;background:#fbfbfb;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>"
        f"<div style='font-size:18px;font-weight:700;'>{task['title']}</div>"
        f"<div style='font-size:14px;color:#666;'>{task['status']}</div>"
        f"</div>"
        f"<div style='margin-bottom:8px;font-size:14px;color:#444;'>{task['note']}</div>"
        f"<div style='display:flex;gap:12px;font-size:13px;color:#555;margin-bottom:8px;'>"
        f"<div><strong>카테고리:</strong> {category.get('name', '미분류')}</div>"
        f"<div><strong>시작:</strong> {start_text}</div>"
        f"<div><strong>종료:</strong> {end_text}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if task["status"] == "할 일":
        cols = st.columns([3, 1, 1])
        key_start = f"start_time_{task['id']}"
        start_time = st.session_state.get(key_start, datetime.now())
        start_time = cols[0].datetime_input("착수 시간", value=start_time, key=key_start)
        if cols[1].button("작업 착수", key=f"start_{task['id']}"):
            start_task(task["id"], start_time)
            st.toast("작업이 진행 중으로 이동했습니다.", icon="✅")
            st.rerun()
        if cols[2].button("삭제", key=f"delete_{task['id']}"):
            delete_task(task["id"])
            st.rerun()
    elif task["status"] == "진행 중":
        cols = st.columns([3, 1, 1])
        key_end = f"end_time_{task['id']}"
        end_time = st.session_state.get(key_end, datetime.now())
        end_time = cols[0].datetime_input("완료 시간", value=end_time, key=key_end)
        if cols[1].button("작업 완료", key=f"complete_{task['id']}"):
            complete_task(task["id"], end_time)
            st.toast("작업이 완료되었습니다.", icon="✅")
            st.rerun()
        if cols[2].button("삭제", key=f"delete_{task['id']}"):
            delete_task(task["id"])
            st.rerun()
    else:
        cols = st.columns([5, 1])
        if cols[1].button("삭제", key=f"delete_{task['id']}"):
            delete_task(task["id"])
            st.rerun()


def build_trend_table() -> str:
    completed_tasks = [
        task for task in st.session_state.tasks
        if task["status"] == "완료" and task["start_time"] and task["end_time"]
    ]
    if not completed_tasks:
        return "<p>완료된 작업이 아직 없습니다.</p>"

    trend: dict[str, dict[int, set[str]]] = {}
    task_index: dict[str, dict[str, Any]] = {task["id"]: task for task in completed_tasks}

    for task in completed_tasks:
        current = task["start_time"]
        end = task["end_time"]
        while current < end:
            date_key = current.date().isoformat()
            date_hours = trend.setdefault(date_key, {hour: set() for hour in range(24)})
            date_hours[current.hour].add(task["id"])
            current += timedelta(minutes=15)

    html = [
        "<div style='overflow-x:auto;'>",
        "<table style='border-collapse:collapse;width:100%;font-size:13px;'>",
        "<thead><tr><th style='padding:8px;border-bottom:2px solid #ddd;text-align:left;'>날짜</th>"
    ] + [
        f"<th style='padding:8px;border-bottom:2px solid #ddd;text-align:center;'>{h:02d}</th>" for h in range(24)
    ] + ["</tr></thead><tbody>"]

    for date_key, hours in sorted(trend.items(), reverse=True):
        html.append(f"<tr><td style='padding:8px;border-bottom:1px solid #eee;font-weight:700;'>{date_key}</td>")
        for hour in range(24):
            hour_task_ids = hours.get(hour, set())
            if hour_task_ids:
                cells = []
                for task_id in sorted(hour_task_ids):
                    task = task_index[task_id]
                    category = st.session_state.categories.get(task["category_id"], {})
                    color = category.get("color", "#999999")
                    title = task["title"]
                    cells.append(
                        f"<div style='background:{color};color:#fff;padding:2px 4px;border-radius:4px;margin-bottom:2px;font-size:10px;line-height:1.2;'>"
                        f"{title}</div>"
                    )
                html.append(
                    f"<td style='padding:4px;border-bottom:1px solid #eee;background:#f8f8f8;vertical-align:top;min-width:40px;'>"
                    f"{''.join(cells)}</td>"
                )
            else:
                html.append("<td style='padding:4px;border-bottom:1px solid #eee;background:#fff;min-width:40px;'></td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")
    return "".join(html)


def build_category_summary() -> str:
    completed_tasks = [
        task for task in st.session_state.tasks
        if task["status"] == "완료" and task["start_time"] and task["end_time"]
    ]
    if not completed_tasks:
        return "<p>완료된 작업이 없습니다.</p>"

    summary: dict[str, dict[str, Any]] = {}
    for task in completed_tasks:
        category_id = task["category_id"]
        category = st.session_state.categories.get(category_id, {})
        duration = int((task["end_time"] - task["start_time"]).total_seconds() / 60)
        entry = summary.setdefault(category_id, {
            "name": category.get("name", "미분류"),
            "color": category.get("color", "#999999"),
            "minutes": 0,
        })
        entry["minutes"] += max(duration, 0)

    html = ["<div style='display:flex;flex-wrap:wrap;gap:12px;margin-top:16px;'>"]
    for entry in summary.values():
        hours = entry["minutes"] // 60
        minutes = entry["minutes"] % 60
        html.append(
            f"<div style='flex:1 1 220px;border:1px solid #ddd;border-radius:12px;padding:14px;background:#fff;'>"
            f"<div style='font-size:15px;font-weight:700;margin-bottom:6px;color:{entry['color']};'>"
            f"{entry['name']}</div>"
            f"<div style='font-size:12px;color:#333;'>총 작업 시간</div>"
            f"<div style='font-size:20px;font-weight:700;margin-top:6px;'>{hours}h {minutes}m</div>"
            f"</div>"
        )
    html.append("</div>")
    return "".join(html)


def render_tasks_tab() -> None:
    st.header("할 일 관리")
    with st.expander("카테고리 추가 / 관리"):
        col1, col2, col3 = st.columns([3, 2, 1])
        category_name = col1.text_input("카테고리 이름", key="new_category_name")
        category_color = col2.color_picker("카테고리 색상", value="#2E86AB", key="new_category_color")
        if col3.button("추가", key="add_category") and category_name.strip():
            add_category(category_name.strip(), category_color)
            st.toast("카테고리가 추가되었습니다.", icon="✅")

        if st.session_state.categories:
            st.markdown("### 현재 카테고리")
            for category_id, category in st.session_state.categories.items():
                row_cols = st.columns([4, 1])
                row_cols[0].markdown(
                    f"<span style='display:inline-flex;align-items:center;padding:6px 10px;border-radius:10px;background:{category['color']};color:#fff;'>"
                    f"{CATEGORY_ICON} {category['name']}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                if row_cols[1].button("삭제", key=f"del_cat_{category_id}"):
                    delete_category(category_id)
                    st.rerun()

    st.markdown("---")
    st.subheader("새 할 일 추가")
    if "task_title" not in st.session_state:
        st.session_state.task_title = ""
    if "task_note" not in st.session_state:
        st.session_state.task_note = ""
    if "task_category" not in st.session_state:
        st.session_state.task_category = list(st.session_state.categories.keys())[0]

    with st.form(key="task_form"):
        st.text_input("작업 제목", key="task_title")
        st.selectbox(
            "카테고리",
            options=list(st.session_state.categories.keys()),
            format_func=lambda cid: st.session_state.categories[cid]["name"],
            key="task_category",
            index=list(st.session_state.categories.keys()).index(st.session_state.task_category),
        )
        st.text_area("설명", key="task_note")
        st.form_submit_button("할 일 추가", on_click=submit_new_task)

    st.markdown("---")
    todo_tasks = [task for task in st.session_state.tasks if task["status"] == "할 일"]
    doing_tasks = [task for task in st.session_state.tasks if task["status"] == "진행 중"]

    st.subheader("할 일 목록")
    if todo_tasks:
        for task in todo_tasks:
            render_task_card(task)
    else:
        st.info("할 일이 없습니다. 새 작업을 추가해주세요.")

    st.subheader("진행 중")
    if doing_tasks:
        for task in doing_tasks:
            render_task_card(task)
    else:
        st.info("진행 중인 작업이 없습니다.")


def render_trend_tab() -> None:
    st.header("완료 트렌드 보기")
    st.write("완료된 작업만 트렌드에서 확인하며, 같은 시간대 중첩도 가능합니다.")
    trend_html = build_trend_table()
    st.markdown(trend_html, unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("카테고리별 작업 시간 요약")
    summary_html = build_category_summary()
    st.markdown(summary_html, unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Streamlit To-Do 앱", page_icon="🗂️", layout="wide")
    init_state()

    st.title("Streamlit 할 일 앱")
    st.markdown(
        "이 앱은 할 일 입력 -> 작업 착수 -> 작업 완료 흐름을 지원하며, 완료된 작업은 트렌드에서 확인할 수 있습니다."
    )

    tab_tasks, tab_trend = st.tabs(["할 일 관리", "완료 트렌드"])
    with tab_tasks:
        render_tasks_tab()
    with tab_trend:
        render_trend_tab()


if __name__ == "__main__":
    main()
