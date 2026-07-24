/** Primary app navigation — real routes, not homepage anchors. */
export type NavItem = {
  href: string;
  label: string;
  /** Short blurb for the homepage portal grid. */
  blurb: string;
};

export const PRIMARY_NAV: NavItem[] = [
  { href: "/", label: "Command", blurb: "Health score, headline KPIs, fiscal pulse." },
  { href: "/themes", label: "Themes", blurb: "Mayoral / City of Hope agenda with live evidence." },
  { href: "/pulse", label: "Pulse", blurb: "What moved this period — live vs demonstration." },
  { href: "/ask", label: "Ask", blurb: "Natural-language questions over retrieved facts." },
  { href: "/briefing", label: "Briefing", blurb: "Today's strategic read — pressure and watch." },
  { href: "/sectors", label: "Sectors", blurb: "Critical operating spine: health, water, safety…" },
  { href: "/compare", label: "Compare", blurb: "Headline contrasts that earn a decision." },
  { href: "/wins", label: "Wins", blurb: "Delivery the City can stand on." },
  { href: "/risks", label: "Risks", blurb: "Ranked risks with drill-down reports." },
  { href: "/opportunities", label: "Opportunities", blurb: "Underspend and redeploy options." },
  { href: "/act", label: "Actions", blurb: "Tracker, decisions, and value delivered." },
  { href: "/simulate", label: "Simulate", blurb: "What-if scenarios on budget and services." },
  { href: "/CPT/domains", label: "Explore", blurb: "Source-linked domain intelligence." },
  { href: "/sources", label: "Sources", blurb: "Feed status and reasoning agents." },
];
