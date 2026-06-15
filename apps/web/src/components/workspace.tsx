import { CenterPanel } from "./center-panel";
import { SourcesPanel } from "./sources-panel";
import { StudioPanel } from "./studio-panel";
import { TopBar } from "./top-bar";

export function Workspace() {
  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <TopBar />
      <main className="flex flex-1 gap-3 overflow-hidden px-3 pb-3">
        <SourcesPanel />
        <CenterPanel />
        <StudioPanel />
      </main>
    </div>
  );
}
