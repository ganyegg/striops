import AppPage, { BackendDown } from "@/components/AppPage";
import CityThemes from "@/components/CityThemes";
import { getThemes } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ThemesPage() {
  try {
    const themes = await getThemes();
    return (
      <AppPage
        crumb="Themes"
        eyebrow="Mayor's agenda"
        title="City themes"
        lead="City of Hope priorities mapped to live evidence — what reports say, what Striops watches continuously, and what still needs an extract."
        wide
      >
        <CityThemes report={themes} />
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
