import { useState, useMemo } from "react";

interface MeetingCalendarProps {
  meetingDates: string[]; // ISO date strings
  onDateClick?: (date: string) => void;
}

function daysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function startDayOfWeek(year: number, month: number): number {
  return new Date(year, month, 1).getDay();
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const DAY_LABELS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export default function MeetingCalendar({ meetingDates, onDateClick }: MeetingCalendarProps) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());

  const dateSet = useMemo(() => new Set(meetingDates), [meetingDates]);

  const days = daysInMonth(year, month);
  const offset = startDayOfWeek(year, month);
  const todayStr = now.toISOString().slice(0, 10);

  const prev = () => {
    if (month === 0) { setYear(year - 1); setMonth(11); }
    else setMonth(month - 1);
  };
  const next = () => {
    if (month === 11) { setYear(year + 1); setMonth(0); }
    else setMonth(month + 1);
  };

  return (
    <div className="select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <button onClick={prev} className="px-2 py-1 text-gray-400 hover:text-gray-700 text-sm">&larr;</button>
        <span className="text-sm font-semibold text-gray-700">
          {MONTH_NAMES[month]} {year}
        </span>
        <button onClick={next} className="px-2 py-1 text-gray-400 hover:text-gray-700 text-sm">&rarr;</button>
      </div>

      {/* Day labels */}
      <div className="grid grid-cols-7 text-center text-xs text-gray-400 mb-1">
        {DAY_LABELS.map((d) => <div key={d}>{d}</div>)}
      </div>

      {/* Day grid */}
      <div className="grid grid-cols-7 text-center text-xs gap-y-0.5">
        {Array.from({ length: offset }).map((_, i) => <div key={`e-${i}`} />)}
        {Array.from({ length: days }).map((_, i) => {
          const day = i + 1;
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const hasMeeting = dateSet.has(dateStr);
          const isToday = dateStr === todayStr;
          const isFuture = dateStr > todayStr;

          return (
            <button
              key={day}
              onClick={() => hasMeeting && onDateClick?.(dateStr)}
              className={`relative w-7 h-7 mx-auto rounded-full flex items-center justify-center transition-colors
                ${isToday ? "ring-1 ring-blue-400" : ""}
                ${hasMeeting ? "cursor-pointer hover:bg-blue-100 font-semibold text-gray-800" : "text-gray-400 cursor-default"}
                ${isFuture && hasMeeting ? "text-blue-700" : ""}
              `}
            >
              {day}
              {hasMeeting && (
                <span className={`absolute bottom-0.5 w-1 h-1 rounded-full ${isFuture ? "bg-blue-500" : "bg-green-500"}`} />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
