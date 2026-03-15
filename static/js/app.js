/**
 * トラブル＆ナレッジ記録 - フロントエンドロジック
 */

document.addEventListener("DOMContentLoaded", () => {
  const recordForm = document.getElementById("record-form");
  const searchInput = document.getElementById("search-input");
  const searchClear = document.getElementById("search-clear");
  const searchMeta = document.getElementById("search-meta");
  const recordsContainer = document.getElementById("records-container");
  const emptyState = document.getElementById("empty-state");
  const emptyMessage = document.getElementById("empty-message");
  const totalCount = document.getElementById("total-count");
  const toastContainer = document.getElementById("toast-container");
  const deleteModal = document.getElementById("delete-modal");
  const cancelDeleteBtn = document.getElementById("cancel-delete");
  const confirmDeleteBtn = document.getElementById("confirm-delete");
  const toggleFormBtn = document.getElementById("toggle-form-btn");
  const formToggle = document.getElementById("form-toggle");
  const exportBtn = document.getElementById("export-btn");
  const exportDropdown = document.getElementById("export-dropdown");

  let deleteTargetId = null;
  let searchDebounceTimer = null;

  loadRecords();

  // エクスポートボタン
  exportBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isVisible = exportDropdown.style.display === "block";
    exportDropdown.style.display = isVisible ? "none" : "block";
  });

  // エクスポートオプション選択
  exportDropdown.querySelectorAll(".export-option").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const format = btn.dataset.format;
      const query = searchInput.value.trim();
      let url = `/api/records/export?format=${format}`;
      if (query) url += `&q=${encodeURIComponent(query)}`;
      exportDropdown.style.display = "none";

      const mimeTypes = {
        csv: { description: "CSV ファイル", accept: { "text/csv": [".csv"] } },
        json: { description: "JSON ファイル", accept: { "application/json": [".json"] } },
        txt: { description: "テキストファイル", accept: { "text/plain": [".txt"] } },
      };

      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error("エクスポートに失敗しました。");
        const blob = await res.blob();

        // File System Access API 対応ブラウザ（Chrome/Edge）
        if (window.showSaveFilePicker) {
          try {
            const handle = await window.showSaveFilePicker({
              suggestedName: `knowledge_export.${format}`,
              types: [mimeTypes[format]],
            });
            const writable = await handle.createWritable();
            await writable.write(blob);
            await writable.close();
            showToast(`ファイルを保存しました！`, "success");
            return;
          } catch (pickerErr) {
            // ユーザーがキャンセルした場合
            if (pickerErr.name === "AbortError") {
              showToast("保存がキャンセルされました。", "info");
              return;
            }
            // それ以外のエラーはフォールバック
          }
        }

        // フォールバック: 通常のダウンロード
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `knowledge_export.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
        showToast(`${format.toUpperCase()} ファイルをダウンロードしました！`, "success");
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  });

  // ドロップダウン外クリックで閉じる
  document.addEventListener("click", (e) => {
    if (!exportBtn.contains(e.target) && !exportDropdown.contains(e.target)) {
      exportDropdown.style.display = "none";
    }
  });

  formToggle.addEventListener("click", () => {
    const isHidden = recordForm.classList.contains("hidden");
    if (isHidden) {
      recordForm.classList.remove("hidden");
      toggleFormBtn.classList.remove("collapsed");
    } else {
      recordForm.classList.add("hidden");
      toggleFormBtn.classList.add("collapsed");
    }
  });

  recordForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = {
      phenomenon: document.getElementById("phenomenon").value.trim(),
      cause: document.getElementById("cause").value.trim(),
      response: document.getElementById("response").value.trim(),
      future_note: document.getElementById("future_note").value.trim(),
    };
    if (!data.phenomenon || !data.cause || !data.response || !data.future_note) {
      showToast("すべての項目を入力してください。", "error");
      return;
    }
    const submitBtn = document.getElementById("btn-submit");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<svg class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> 保存中...`;
    try {
      const res = await fetch("/api/records", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
      if (!res.ok) { const err = await res.json(); throw new Error(err.error || "保存に失敗しました。"); }
      recordForm.reset();
      showToast("記録を保存しました！", "success");
      loadRecords();
    } catch (err) { showToast(err.message, "error"); }
    finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg> 記録を保存`;
    }
  });

  searchInput.addEventListener("input", () => {
    const val = searchInput.value.trim();
    searchClear.style.display = val ? "flex" : "none";
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => loadRecords(val), 300);
  });

  searchClear.addEventListener("click", () => {
    searchInput.value = "";
    searchClear.style.display = "none";
    searchMeta.textContent = "";
    loadRecords();
    searchInput.focus();
  });

  async function loadRecords(query = "") {
    try {
      const url = query ? `/api/records?q=${encodeURIComponent(query)}` : "/api/records";
      const res = await fetch(url);
      if (!res.ok) throw new Error("記録の読み込みに失敗しました。");
      const records = await res.json();
      renderRecords(records, query);
    } catch (err) { showToast(err.message, "error"); }
  }

  function renderRecords(records, query = "") {
    totalCount.textContent = records.length;
    if (records.length === 0) {
      recordsContainer.innerHTML = "";
      emptyState.style.display = "block";
      if (query) {
        emptyMessage.innerHTML = `「<strong>${escapeHtml(query)}</strong>」に一致する記録はありません。`;
        searchMeta.textContent = `0 件の検索結果`;
      } else {
        emptyMessage.innerHTML = "まだ記録がありません。<br>上のフォームから最初の記録を追加しましょう。";
        searchMeta.textContent = "";
      }
      return;
    }
    emptyState.style.display = "none";
    searchMeta.textContent = query ? `${records.length} 件の検索結果` : "";
    recordsContainer.innerHTML = records.map((r, i) => createRecordCard(r, query, i)).join("");
    recordsContainer.querySelectorAll("[data-delete-id]").forEach((btn) => {
      btn.addEventListener("click", () => { deleteTargetId = btn.dataset.deleteId; deleteModal.style.display = "flex"; });
    });
  }

  function createRecordCard(record, query, index) {
    const date = formatDate(record.created_at);
    const delay = Math.min(index * 0.06, 0.6);
    const highlight = (text) => {
      if (!query) return escapeHtml(text);
      const escaped = escapeHtml(text);
      const escapedQuery = escapeHtml(query);
      const regex = new RegExp(`(${escapeRegex(escapedQuery)})`, "gi");
      return escaped.replace(regex, "<mark>$1</mark>");
    };
    return `
      <div class="record-card" style="animation-delay: ${delay}s">
        <div class="card-header">
          <div class="card-date">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            ${date}
          </div>
          <button class="btn-icon" data-delete-id="${record.id}" title="この記録を削除">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
        <div class="card-body">
          <div class="card-field card-field-phenomenon"><div class="card-field-label"><span class="dot dot-phenomenon"></span>事象</div><div class="card-field-text">${highlight(record.phenomenon)}</div></div>
          <div class="card-field card-field-cause"><div class="card-field-label"><span class="dot dot-cause"></span>原因の推測</div><div class="card-field-text">${highlight(record.cause)}</div></div>
          <div class="card-field card-field-response"><div class="card-field-label"><span class="dot dot-response"></span>現場の対応</div><div class="card-field-text">${highlight(record.response)}</div></div>
          <div class="card-field card-field-future"><div class="card-field-label"><span class="dot dot-future"></span>未来の自分への指示</div><div class="card-field-text">${highlight(record.future_note)}</div></div>
        </div>
      </div>`;
  }

  cancelDeleteBtn.addEventListener("click", () => { deleteModal.style.display = "none"; deleteTargetId = null; });

  confirmDeleteBtn.addEventListener("click", async () => {
    if (!deleteTargetId) return;
    try {
      const res = await fetch(`/api/records/${deleteTargetId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("削除に失敗しました。");
      deleteModal.style.display = "none"; deleteTargetId = null;
      showToast("記録を削除しました。", "info");
      loadRecords(searchInput.value.trim());
    } catch (err) { showToast(err.message, "error"); }
  });

  deleteModal.addEventListener("click", (e) => { if (e.target === deleteModal) { deleteModal.style.display = "none"; deleteTargetId = null; } });

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icons = {
      success: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`,
      error: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
      info: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`,
    };
    toast.innerHTML = `${icons[type] || icons.info} ${escapeHtml(message)}`;
    toastContainer.appendChild(toast);
    setTimeout(() => { toast.style.animation = "toastOut 0.3s ease forwards"; setTimeout(() => toast.remove(), 300); }, 3000);
  }

  function formatDate(iso) {
    const d = new Date(iso);
    return `${d.getFullYear()}/${String(d.getMonth()+1).padStart(2,"0")}/${String(d.getDate()).padStart(2,"0")} ${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}`;
  }

  function escapeHtml(str) { const div = document.createElement("div"); div.textContent = str; return div.innerHTML; }
  function escapeRegex(str) { return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
});

const style = document.createElement("style");
style.textContent = `@keyframes spin { to { transform: rotate(360deg); } } .spin { animation: spin 0.8s linear infinite; }`;
document.head.appendChild(style);
