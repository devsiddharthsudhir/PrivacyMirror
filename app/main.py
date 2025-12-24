from __future__ import annotations

import sys
import json
from pathlib import Path

# ✅ Add project root (ethical-mirror/) to Python import path
# IMPORTANT: use append (not insert(0)) to avoid shadowing numpy/pandas from site-packages
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import streamlit as st

from core.pipeline import ImportConfig, run_pipeline
from core.security.vault import DEFAULT_VAULT, load_encrypted, save_encrypted, wipe_vault

st.set_page_config(page_title="Ethical Mirror", page_icon="🪞", layout="wide")

st.title("🪞 Ethical Mirror")
st.caption("Offline privacy risk dashboard — you choose what to scan, nothing leaves your machine.")

with st.expander("✅ Consent & Safety", expanded=True):
    st.markdown(
        """
**This tool must only be used on your own data, with your explicit consent.**

- Ethical Mirror runs locally and does not upload anything.
- You explicitly choose files/folders to analyze.
- Raw content is processed in-memory unless you choose to save an encrypted summary.
        """
    )
    consent = st.checkbox("I understand and I consent to analyze my own data locally.", value=False)

if not consent:
    st.stop()

st.subheader("1) Choose your data sources")

col1, col2 = st.columns(2)
with col1:
    mbox_path = st.text_input(
        "Email (MBOX) file path (optional)",
        placeholder=r"C:\path\to\mail.mbox or /path/to/mail.mbox",
    )
    eml_dir = st.text_input(
        "Email (EML) folder path (optional)",
        placeholder=r"C:\path\to\eml_folder or /path/to/eml_folder",
    )
    notes_dir = st.text_input(
        "Notes folder path (txt/md) (optional)",
        placeholder=r"C:\path\to\notes or /path/to/notes",
    )
with col2:
    browser_sqlite = st.text_input(
        "Browser History SQLite path (Chrome/Edge) (optional)",
        placeholder=r"C:\path\to\History or /path/to/History",
    )
    st.info(
        "Tip: if Chrome says the History file is locked, close the browser or import a copy. "
        "See docs/importing_browser_history.md"
    )

with st.expander("Advanced: import limits (for huge datasets)"):
    lim_mbox = st.number_input("Max emails from MBOX", 100, 20000, 5000, 100)
    lim_eml = st.number_input("Max EML files", 100, 20000, 5000, 100)
    lim_notes = st.number_input("Max note files", 100, 20000, 5000, 100)
    lim_browser = st.number_input("Max browser visits", 100, 50000, 10000, 500)

analyze = st.button("🔎 Analyze locally", type="primary")

if "report" not in st.session_state:
    st.session_state.report = None

if analyze:
    cfg = ImportConfig(
        mbox_path=Path(mbox_path).expanduser() if mbox_path.strip() else None,
        eml_dir=Path(eml_dir).expanduser() if eml_dir.strip() else None,
        notes_dir=Path(notes_dir).expanduser() if notes_dir.strip() else None,
        browser_history_sqlite=Path(browser_sqlite).expanduser() if browser_sqlite.strip() else None,
    )
    with st.spinner("Analyzing... (offline)"):
        docs, report = run_pipeline(
            cfg,
            limits={"mbox": lim_mbox, "eml": lim_eml, "notes": lim_notes, "browser": lim_browser},
        )
    st.session_state.report = report
    st.success(f"Done. Analyzed {len(docs)} items across: {', '.join(report['summary']['sources']) or 'none'}")

report = st.session_state.report
if not report:
    st.stop()

st.subheader("2) Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Interests", "Daily Rhythm", "Work Patterns", "Signals & Attribution", "Minimization Tips"]
)

with tab1:
    st.markdown("### Top inferred interest areas")
    rows = [{"Interest": x["label"], "Strength (%)": round(x["score"] * 100, 2)} for x in report["interests"]]
    if rows:
        df = pd.DataFrame(rows).sort_values("Strength (%)", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Not enough signals to infer interests yet.")

    for it in report["interests"]:
        with st.expander(f"🧩 {it['label']}  •  strength {it['score']*100:.1f}%"):
            st.write("Top keywords:", ", ".join([f"{k}({int(v)})" for k, v in it["top_keywords"]]) or "—")
            st.write("Top sources:")
            st.json(it["top_sources"])

with tab2:
    r = report["rhythm"]
    st.markdown("### Daily rhythm (based on timestamps)")
    st.metric("Chronotype", r["inferred_chronotype"])
    st.metric("Confidence", f"{r['confidence']:.2f}")
    st.write(f"Peak activity hour: **{r['peak_hour']}**")
    st.write(f"Earliest active hour (approx): **{r['earliest_active_hour']}**")
    st.write(f"Latest active hour (approx): **{r['latest_active_hour']}**")

    dfh = (
        pd.DataFrame({"hour": list(r["hourly_counts"].keys()), "events": list(r["hourly_counts"].values())})
        .sort_values("hour")
    )
    st.bar_chart(dfh.set_index("hour"))

    dfd = (
        pd.DataFrame({"weekday": list(r["day_counts"].keys()), "events": list(r["day_counts"].values())})
        .sort_values("weekday")
    )
    st.bar_chart(dfd.set_index("weekday"))

with tab3:
    wpat = report["work_patterns"]
    st.markdown("### Work patterns (heuristic)")
    st.metric("Weekday activity ratio", f"{wpat['weekday_ratio']*100:.1f}%")
    st.metric("Weekend activity ratio", f"{wpat['weekend_ratio']*100:.1f}%")
    st.write("Typical work window (guess):", wpat["typical_work_start"], "→", wpat["typical_work_end"])
    st.write("Meeting-hour guess:", wpat["meeting_hour_guess"])
    st.metric("Confidence", f"{wpat['confidence']:.2f}")

with tab4:
    st.markdown("### Why these inferences?")
    st.caption("Attribution here is keyword-signal based (offline, transparent).")
    if not report["attributions"]:
        st.info("No attributions available yet. Import more data sources for richer signals.")
    for a in report["attributions"]:
        with st.expander(f"🔍 {a['inference']}"):
            st.write("Strongest signals:")
            st.json(a["signals"])
            st.write("Top supporting items:")
            st.json(a["top_documents"])

with tab5:
    st.markdown("### Reduction strategies")
    for tip in report["minimization_tips"]:
        with st.expander(f"✅ {tip['title']}"):
            st.write(tip["why"])
            st.write("Do this:")
            for x in tip["do_this"]:
                st.write("- ", x)

st.subheader("3) Export / Secure storage (optional)")

colA, colB = st.columns(2)

with colA:
    st.download_button(
        "⬇️ Download report JSON",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name="ethical_mirror_report.json",
        mime="application/json",
    )

with colB:
    st.markdown("#### Encrypted local vault")
    st.caption(f"Vault file location: `{DEFAULT_VAULT}`")
    passphrase = st.text_input(
        "Vault passphrase",
        type="password",
        help="Used to encrypt/decrypt a summary report on this machine.",
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔐 Save encrypted summary"):
            if not passphrase:
                st.error("Enter a passphrase first.")
            else:
                save_encrypted(report, passphrase)
                st.success("Saved encrypted summary.")
    with c2:
        if st.button("🔓 Load from vault"):
            if not passphrase:
                st.error("Enter a passphrase first.")
            else:
                try:
                    loaded = load_encrypted(passphrase)
                    st.session_state.report = loaded
                    st.success("Loaded report from vault.")
                except Exception as e:
                    st.error(f"Could not load: {e}")
    with c3:
        if st.button("🧨 Wipe vault"):
            wipe_vault()
            st.success("Vault wiped (if it existed).")
