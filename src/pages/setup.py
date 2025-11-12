"""page d'affichage du loader pendant l'initialisation des données."""

from __future__ import annotations

from typing import Iterable
from dash import html

STEP_FLOW = [
    "initialisation des données",
    "téléchargement du csv",
    "initialisation de la base sqlite",
    "vérification des données",
    "initialisation terminée",
]


def _progress_ratio(step: str | None, success: bool) -> float:
    """calcule la progression globale à partir de l'étape courante."""
    if success:
        return 1.0
    if not step or step not in STEP_FLOW:
        return 0.0
    index = STEP_FLOW.index(step)
    ratio = (index + 1) / len(STEP_FLOW)
    return min(max(ratio, 0.0), 1.0)


def _extract_seen_steps(messages: Iterable[str]) -> list[str]:
    """retourne la liste des étapes vues dans les messages [STEP]."""
    msgs = list(messages)[-50:]
    return [m[7:].strip() for m in msgs if m.startswith("[STEP] ")]


def _status_texts(
    clean_step: str | None, completed: bool, success: bool
) -> tuple[str, str]:
    """détermine les textes de statut et d'aide."""
    if not completed:
        return (
            clean_step or "initialisation en cours...",
            "merci de patienter pendant la préparation des données.",
        )
    if success:
        return "initialisation terminée.", "redirection vers l'accueil en cours..."
    status = "une erreur est survenue pendant l'initialisation."
    help_text = (
        clean_step
        if clean_step and clean_step not in STEP_FLOW
        else "consultez le journal ci-dessous puis relancez l'application."
    )
    return status, help_text


def _build_progress_bar(percent: int) -> html.Div:
    """barre de progression stylée."""
    return html.Div(
        [html.Div(style={
            "width": f"{percent}%",
            "height": "100%",
            "background": "linear-gradient(90deg,#2d9cdb,#27ae60)",
            "borderRadius": "999px",
            "transition": "width 0.6s ease",
        })],
        style={
            "height": "14px",
            "width": "100%",
            "backgroundColor": "#e4e7eb",
            "borderRadius": "999px",
            "overflow": "hidden",
            "boxShadow": "inset 0 1px 3px rgba(0,0,0,0.12)",
        },
    )


def _build_steps_summary(percent: int, clean_step: str | None) -> html.Div:
    """ligne récap % + étape courante."""
    return html.Div(
        [
            html.Strong(f"{percent}%"),
            html.Span(
                f" - {clean_step or 'initialisation en cours...'}",
                style={"marginLeft": "8px"},
            ),
        ],
        style={"marginTop": "12px", "fontSize": "16px", "color": "#1f2933"},
    )


def _build_step_list(
    clean_step: str | None, seen_steps: list[str], completed: bool, success: bool
) -> html.Div:
    """liste des étapes avec préfixes."""
    def prefix(step: str) -> str:
        if success:
            return "[x]"
        if step == clean_step and not completed:
            return "[>]"
        if step in seen_steps:
            return "[x]"
        return "[ ]"

    return html.Div(
        [
            html.Div(
                f"{prefix(step)} {step}",
                style={
                    "padding": "4px 0",
                    "color": "#1f2933" if step in seen_steps or success else "#7b8794",
                    "fontWeight": "600" if step == clean_step else "400",
                },
            )
            for step in STEP_FLOW
        ],
        style={"marginTop": "16px"},
    )


def render_setup_page(
    messages: Iterable[str],
    current_step: str | None,
    *,
    completed: bool,
    success: bool,
) -> html.Div:
    """construit la page affichée pendant l'initialisation des données."""
    seen_steps = _extract_seen_steps(messages)
    last_seen = seen_steps[-1] if seen_steps else None
    clean_step = current_step or last_seen

    ratio = _progress_ratio(clean_step, success)
    percent = int(ratio * 100)

    status_text, help_text = _status_texts(clean_step, completed, success)
    progress_bar = _build_progress_bar(percent)
    steps_summary = _build_steps_summary(percent, clean_step)
    step_list = _build_step_list(clean_step, seen_steps, completed, success)

    content = html.Div(
        [
            html.H2("préparation des données",
                    style={"marginBottom": "16px", "color": "#102a43"}),
            html.P(status_text, style={"fontSize": "18px", "color": "#334155"}),
            html.P(help_text, style={"marginBottom": "24px", "color": "#52606d"}),
            progress_bar,
            steps_summary,
            step_list,
        ],
        style={
            "maxWidth": "640px",
            "margin": "60px auto",
            "padding": "32px",
            "backgroundColor": "white",
            "borderRadius": "12px",
            "boxShadow": "0 12px 32px rgba(15,23,42,0.12)",
            "border": "1px solid #e4e7eb",
        },
    )

    return html.Div(
        content,
        style={
            "background": "linear-gradient(135deg,#f3f4f6,#e0f2f1)",
            "minHeight": "100vh",
            "padding": "40px 16px",
        },
    )
