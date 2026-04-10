export function NotesPanel({
  notes,
}: Readonly<{
  notes: { section: string; line: string }[];
}>) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <span className="eyebrow">Report Notes</span>
          <h2>원문 메모</h2>
        </div>
        <p>리포트에서 추출한 핵심 문장을 빠르게 확인할 수 있습니다.</p>
      </div>
      <div className="notes-list">
        {notes.length ? (
          notes.map((note, index) => (
            <div key={`${note.section}-${index}`} className="note-card">
              <span>{note.section}</span>
              <p>{note.line}</p>
            </div>
          ))
        ) : (
          <div className="empty-card">추출된 메모가 없습니다.</div>
        )}
      </div>
    </div>
  );
}
