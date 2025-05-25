// 頂部導航功能
function initNavigation() {
    const navItems = document.querySelectorAll('.navbar-links li');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            // 更新活動狀態
            navItems.forEach(li => li.classList.remove('active'));
            this.classList.add('active');
            
            // 頁面切換邏輯
            const pageId = this.getAttribute('data-page');
            switchPage(pageId);
        });
    });
}

// 頁面切換控制
function switchPage(pageId) {
    // 隱藏所有頁面
    document.querySelectorAll('.page-content').forEach(page => {
        page.style.display = 'none';
    });
    
    // 顯示當前頁面

    if(pageId === 'members') {
        animateMemberCards();
    }

    if (pageId === 'training') {
        animateTrainingCards();
    }

    if(pageId === 'analysis') {
        document.querySelector('.analysis-section').style.display = 'block';
        initParticles();
    } else {
        document.querySelector('.analysis-section').style.display = 'none';
        document.getElementById(`${pageId}-page`).style.display = 'block';
    }
    
}

// 粒子效果初始化
function initParticles() {
    if (typeof particlesJS !== 'undefined') {
        particlesJS.load('particles-js', '/static/particles-config.json', function () {
            console.log('particles.js config loaded');
        });
    }
}

// 範例資料點擊自動填充
function setupExampleLinks() {
    document.querySelectorAll('.example-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelector('input[name="query"]').value = 
                e.target.textContent.split(' ')[0];
        });
    });
}

// 訓練卡片動畫
function animateTrainingCards() {
    const cards = document.querySelectorAll('.training-card');
    
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateX(' + (index % 2 === 0 ? '-' : '') + '50px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateX(0)';
        }, 300 * index);
    });
}

// 團隊成員卡片動畫
function animateMemberCards() {
    const cards = document.querySelectorAll('.member-card');
    
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(-50px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateX(0)';
        }, 300 * index);
    });
}

// 語言切換功能
// document.getElementById('language-select').addEventListener('change', function() {
//     console.log('切換語言至:', this.value);
//     // 實際語言切換邏輯需自行實現
// });

// 初始化所有功能
document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    setupExampleLinks();
    initParticles();
    
});

// 語言切換
// language.js
class LanguageManager {
  constructor() {
    this.currentLang = document.documentElement.lang || 'zh-TW';
    this.translations = {};
  }

  async loadTranslations(lang) {
    try {
      const response = await fetch(`/get_translations?lang=${lang}`);
      this.translations = await response.json();
      this.applyTranslations();
      this.setCookie('preferred_lang', lang, 365);
      document.documentElement.lang = lang;
    } catch (error) {
      console.error('語言載入失敗:', error);
    }
  }

  applyTranslations() {
    // 遍歷所有帶有data-i18n屬性的元素
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (this.translations[key]) {
        el.textContent = this.translations[key];
      }
    });

    // 處理placeholder等屬性
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (this.translations[key]) {
        el.placeholder = this.translations[key];
      }
    });
  }

  setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days*24*60*60*1000));
    document.cookie = `${name}=${value};expires=${date.toUTCString()};path=/`;
  }
}

// 初始化
// const languageManager = new LanguageManager();

// 語言切換按鈕事件
// document.getElementById('language-select').addEventListener('change', (e) => {
//   const lang = e.target.value;
//   languageManager.loadTranslations(lang);
// });

// 頁面載入時應用語言
// document.addEventListener('DOMContentLoaded', () => {
//   const preferredLang = document.cookie.replace(/(?:(?:^|.*;\s*)preferred_lang\s*=\s*([^;]*).*$)|^.*$/, '$1') || 'zh-TW';
//   languageManager.loadTranslations(preferredLang);
// });