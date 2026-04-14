interface Props {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export default function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="data-toolbar" style={{ borderTop: "1px solid var(--border)", borderBottom: "0" }}>
      <span className="data-note">
        {total === 0
          ? "No results"
          : `Showing ${from.toLocaleString()}-${to.toLocaleString()} of ${total.toLocaleString()}`}
      </span>
      <div className="page-actions">
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="form-control"
          style={{ width: 120, minWidth: 120 }}
        >
          {[25, 50, 100].map((n) => (
            <option key={n} value={n}>
              {n} / page
            </option>
          ))}
        </select>
        <div className="chip-row" style={{ alignItems: "center" }}>
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="button-ghost"
          >
            Prev
          </button>
          <span className="chip-pill active">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="button-ghost"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
