/**
 * ShiftManagerWeb - モダンJavaScriptファイル
 */

// DOMが読み込まれたら実行
document.addEventListener('DOMContentLoaded', function() {
  // 基本機能の初期化
  setupAlertDismiss();
  initPageSpecific();
  initTooltips();
  initAnimations();
  initThemeToggle();
  
  // パフォーマンス向上のための遅延読み込み
  setTimeout(() => {
    initAdvancedFeatures();
  }, 100);
});

/**
 * アラートメッセージの自動非表示設定
 */
function setupAlertDismiss() {
  const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
  
  alerts.forEach((alert, index) => {
    // アニメーション付きで表示
    setTimeout(() => {
      alert.classList.add('slide-in-left');
    }, index * 200);
    
    // 5秒後に自動的に閉じる
    setTimeout(() => {
      alert.style.animation = 'slideOutRight 0.5s ease-in-out forwards';
      setTimeout(() => {
        if (alert.parentNode) {
          alert.remove();
        }
      }, 500);
    }, 5000);
  });
}

/**
 * ページ固有の初期化処理
 */
function initPageSpecific() {
  const currentPath = window.location.pathname;
  
  // アップロードページの場合
  if (currentPath.includes('/upload')) {
    initUploadPage();
  }
  
  // 設定ページの場合
  if (currentPath.includes('/settings')) {
    initSettingsPage();
  }
  
  // 確認ページの場合
  if (currentPath.includes('/confirm')) {
    initConfirmPage();
  }
  
  // イベント一覧ページの場合
  if (currentPath.includes('/events')) {
    initEventsPage();
  }
}

/**
 * アップロードページの初期化
 */
function initUploadPage() {
  const dropArea = document.getElementById('drop-area');
  const fileInput = document.getElementById('file-input');
  const uploadBtn = document.getElementById('upload-btn');
  
  if (!dropArea) return;
  
  // ドラッグ&ドロップ機能の強化
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });
  
  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
  });
  
  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
  });
  
  dropArea.addEventListener('drop', handleDrop, false);
  
  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }
  
  function highlight(e) {
    dropArea.classList.add('dragover');
    dropArea.innerHTML = `
      <div class="text-center">
        <i class="fas fa-cloud-upload-alt fa-4x text-success mb-3 icon-bounce"></i>
        <h4 class="text-success">ファイルをドロップしてください</h4>
        <p class="text-muted">PDFファイルのみ対応</p>
      </div>
    `;
  }
  
  function unhighlight(e) {
    dropArea.classList.remove('dragover');
    resetDropArea();
  }
  
  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf') {
        fileInput.files = files;
        handleFileSelect(file);
      } else {
        showNotification('PDFファイルのみアップロード可能です', 'error');
        resetDropArea();
      }
    }
  }
  
  function resetDropArea() {
    dropArea.innerHTML = `
      <div class="text-center">
        <i class="fas fa-cloud-upload-alt fa-4x text-primary mb-3"></i>
        <h4>PDFファイルをドラッグ&ドロップ</h4>
        <p class="text-muted">または<span class="text-primary">クリックしてファイルを選択</span></p>
        <small class="text-muted">最大ファイルサイズ: 10MB</small>
      </div>
    `;
  }
  
  // ファイル選択時の処理
  if (fileInput) {
    fileInput.addEventListener('change', function() {
      const file = this.files[0];
      if (file) {
        handleFileSelect(file);
      }
    });
  }
  
  function handleFileSelect(file) {
    if (file.type !== 'application/pdf') {
      showNotification('PDFファイルのみアップロード可能です', 'error');
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB
      showNotification('ファイルサイズが大きすぎます（最大10MB）', 'error');
      return;
    }
    
    // ファイル情報表示
    displayFileInfo(file);
    
    // アップロードボタン有効化
    if (uploadBtn) {
      uploadBtn.disabled = false;
      uploadBtn.classList.add('btn-success');
      uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i>アップロード開始';
    }
    
    showNotification('ファイルが選択されました', 'success');
  }
  
  function displayFileInfo(file) {
    const fileInfo = document.getElementById('file-info');
    if (fileInfo) {
      fileInfo.innerHTML = `
        <div class="card border-success">
          <div class="card-body">
            <h6 class="card-title text-success">
              <i class="fas fa-file-pdf me-2"></i>選択されたファイル
            </h6>
            <p class="card-text">
              <strong>ファイル名:</strong> ${file.name}<br>
              <strong>サイズ:</strong> ${formatFileSize(file.size)}<br>
              <strong>最終更新:</strong> ${formatDate(file.lastModified)}
            </p>
          </div>
        </div>
      `;
      fileInfo.style.display = 'block';
      fileInfo.classList.add('fade-in');
    }
  }
  
  // フォーム送信時のローディング表示
  const uploadForm = document.getElementById('upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', function() {
      showLoadingOverlay('PDFを解析中...');
    });
  }
}

/**
 * 設定ページの初期化
 */
function initSettingsPage() {
  // 追加リマインダーのトグル処理
  const additionalReminderCheckbox = document.getElementById('additional_reminder');
  const additionalReminderGroup = document.getElementById('additional_reminder_group');
  
  if (additionalReminderCheckbox && additionalReminderGroup) {
    additionalReminderCheckbox.addEventListener('change', function() {
      if (this.checked) {
        additionalReminderGroup.style.display = 'flex';
        additionalReminderGroup.classList.add('slide-in-left');
      } else {
        additionalReminderGroup.style.animation = 'slideOutLeft 0.3s ease-in-out forwards';
        setTimeout(() => {
          additionalReminderGroup.style.display = 'none';
        }, 300);
      }
    });
  }
  
  // カラーピッカーの視覚的フィードバック
  const colorRadios = document.querySelectorAll('input[name="color_id"]');
  colorRadios.forEach(radio => {
    radio.addEventListener('change', function() {
      // アニメーション付きで選択状態を更新
      document.querySelectorAll('.color-option').forEach(option => {
        option.classList.remove('selected');
      });
      
      if (this.checked) {
        const label = this.closest('.color-option');
        if (label) {
          label.classList.add('selected');
          label.style.animation = 'pulse 0.5s ease-in-out';
        }
      }
    });
  });
  
  // 設定保存時のフィードバック
  const settingsForm = document.getElementById('settings-form');
  if (settingsForm) {
    settingsForm.addEventListener('submit', function() {
      showLoadingOverlay('設定を保存中...');
    });
  }
}

/**
 * 確認ページの初期化
 */
function initConfirmPage() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"][name="selected_shifts"]');
  const submitButton = document.querySelector('button[type="submit"]');
  const selectAllBtn = document.getElementById('select-all');
  const deselectAllBtn = document.getElementById('deselect-all');
  
  if (checkboxes.length && submitButton) {
    // 全選択/全解除ボタン
    if (selectAllBtn) {
      selectAllBtn.addEventListener('click', function() {
        checkboxes.forEach(cb => {
          cb.checked = true;
          animateCheckbox(cb);
        });
        updateSubmitButton();
      });
    }
    
    if (deselectAllBtn) {
      deselectAllBtn.addEventListener('click', function() {
        checkboxes.forEach(cb => {
          cb.checked = false;
          animateCheckbox(cb);
        });
        updateSubmitButton();
      });
    }
    
    // チェックボックスの変更を監視
    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', function() {
        animateCheckbox(this);
        updateSubmitButton();
      });
    });
    
    function animateCheckbox(checkbox) {
      const row = checkbox.closest('tr');
      if (row) {
        if (checkbox.checked) {
          row.classList.add('table-success');
          row.style.animation = 'pulse 0.3s ease-in-out';
        } else {
          row.classList.remove('table-success');
        }
      }
    }
    
    function updateSubmitButton() {
      const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
      submitButton.disabled = checkedCount === 0;
      
      if (checkedCount > 0) {
        submitButton.innerHTML = `<i class="fas fa-calendar-plus me-2"></i>選択した${checkedCount}件を登録`;
        submitButton.classList.remove('btn-secondary');
        submitButton.classList.add('btn-success');
      } else {
        submitButton.innerHTML = '<i class="fas fa-calendar-plus me-2"></i>シフトを選択してください';
        submitButton.classList.remove('btn-success');
        submitButton.classList.add('btn-secondary');
      }
    }
    
    // 初期状態の設定
    updateSubmitButton();
  }
  
  // 確認フォーム送信時
  const confirmForm = document.getElementById('confirm-form');
  if (confirmForm) {
    confirmForm.addEventListener('submit', function() {
      showLoadingOverlay('カレンダーに登録中...');
    });
  }
}

/**
 * イベント一覧ページの初期化
 */
function initEventsPage() {
  // 検索機能
  const searchInput = document.getElementById('event-search');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      const eventRows = document.querySelectorAll('.event-row');
      
      eventRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
          row.style.display = '';
          row.classList.add('fade-in');
        } else {
          row.style.display = 'none';
        }
      });
    });
  }
  
  // 削除確認
  const deleteButtons = document.querySelectorAll('.delete-event');
  deleteButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      const eventTitle = this.dataset.eventTitle;
      
      if (confirm(`「${eventTitle}」を削除しますか？`)) {
        showLoadingOverlay('イベントを削除中...');
        window.location.href = this.href;
      }
    });
  });
}

/**
 * アニメーションの初期化
 */
function initAnimations() {
  // Intersection Observer for scroll animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
      }
    });
  }, observerOptions);
  
  // 監視対象要素を追加
  document.querySelectorAll('.card, .alert, .table').forEach(el => {
    observer.observe(el);
  });
}

/**
 * テーマ切り替え機能
 */
function initThemeToggle() {
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      document.body.classList.toggle('dark-theme');
      const isDark = document.body.classList.contains('dark-theme');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      
      // アイコンの切り替え
      const icon = this.querySelector('i');
      if (isDark) {
        icon.className = 'fas fa-sun';
      } else {
        icon.className = 'fas fa-moon';
      }
    });
    
    // 保存されたテーマを適用
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      document.body.classList.add('dark-theme');
      themeToggle.querySelector('i').className = 'fas fa-sun';
    }
  }
}

/**
 * 高度な機能の初期化
 */
function initAdvancedFeatures() {
  // プログレスバーのアニメーション
  const progressBars = document.querySelectorAll('.progress-bar');
  progressBars.forEach(bar => {
    const width = bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => {
      bar.style.width = width;
    }, 500);
  });
  
  // カウンターアニメーション
  const counters = document.querySelectorAll('.counter');
  counters.forEach(counter => {
    animateCounter(counter);
  });
}

/**
 * ツールチップの初期化
 */
function initTooltips() {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

/**
 * ローディングオーバーレイの表示
 */
function showLoadingOverlay(message = 'Loading...') {
  const overlay = document.createElement('div');
  overlay.id = 'loading-overlay';
  overlay.className = 'loading-overlay';
  overlay.innerHTML = `
    <div class="loading-content">
      <div class="loading-spinner"></div>
      <p class="mt-3">${message}</p>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // アニメーション付きで表示
  setTimeout(() => {
    overlay.classList.add('show');
  }, 10);
}

/**
 * ローディングオーバーレイの非表示
 */
function hideLoadingOverlay() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.remove('show');
    setTimeout(() => {
      overlay.remove();
    }, 300);
  }
}

/**
 * 通知の表示
 */
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} alert-dismissible fade show notification`;
  notification.innerHTML = `
    <i class="fas fa-${getIconForType(type)} me-2"></i>
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  // 通知コンテナがない場合は作成
  let container = document.getElementById('notification-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-container';
    container.className = 'notification-container';
    document.body.appendChild(container);
  }
  
  container.appendChild(notification);
  
  // 自動削除
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

/**
 * タイプに応じたアイコンを取得
 */
function getIconForType(type) {
  const icons = {
    success: 'check-circle',
    error: 'exclamation-triangle',
    warning: 'exclamation-circle',
    info: 'info-circle'
  };
  return icons[type] || 'info-circle';
}

/**
 * カウンターアニメーション
 */
function animateCounter(element) {
  const target = parseInt(element.textContent);
  const duration = 2000;
  const step = target / (duration / 16);
  let current = 0;
  
  const timer = setInterval(() => {
    current += step;
    if (current >= target) {
      current = target;
      clearInterval(timer);
    }
    element.textContent = Math.floor(current);
  }, 16);
}

/**
 * ファイルサイズのフォーマット
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 日付をフォーマットする
 */
function formatDate(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleDateString('ja-JP');
}

/**
 * 時間をフォーマットする
 */
function formatTime(timeString) {
  const date = new Date(timeString);
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

// CSS for loading overlay and notifications
const style = document.createElement('style');
style.textContent = `
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .loading-overlay.show {
    opacity: 1;
  }
  
  .loading-content {
    text-align: center;
    color: white;
  }
  
  .notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1050;
    max-width: 400px;
  }
  
  .notification {
    margin-bottom: 10px;
    animation: slideInRight 0.3s ease-out;
  }
  
  @keyframes slideInRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOutRight {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
  
  @keyframes slideOutLeft {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(-100%);
      opacity: 0;
    }
  }
  
  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
    100% {
      transform: scale(1);
    }
  }
  
  .color-option.selected {
    border: 2px solid var(--primary-color) !important;
    box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
  }
`;
document.head.appendChild(style);

/**
 * 日付をフォーマットする
 * @param {string} dateString - 日付文字列
 * @param {string} format - フォーマット
 * @returns {string} フォーマットされた日付
 */
function formatDate(dateString, format = 'YYYY/MM/DD') {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day);
}

/**
 * 時間をフォーマットする
 * @param {string} timeString - 時間文字列
 * @returns {string} フォーマットされた時間
 */
function formatTime(timeString) {
  const date = new Date(timeString);
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  
 