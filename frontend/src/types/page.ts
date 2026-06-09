export type PageType = "MEETING" | "RETROSPECTIVE";

export type CalendarPageItem = {
  id: number;
  type: PageType;
  title: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
};