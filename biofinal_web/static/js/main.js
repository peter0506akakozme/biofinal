// 頁面切換功能
document.querySelectorAll('.nav-links li').forEach(item => {
  item.addEventListener('click', function() {
    // 移除所有active類
    document.querySelectorAll('.nav-links li').forEach(li => {
      li.classList.remove('active');
    });
    
    // 添加當前active類
    this.classList.add('active');
    
    // 這裡可以添加實際頁面切換邏輯
    const page = this.getAttribute('data-page');
    console.log('切換到頁面:', page);
    
    // 示例：隱藏所有內容，顯示當前頁面
    document.querySelectorAll('.page-content').forEach(content => {
      content.style.display = 'none';
    });
    document.getElementById(`${page}-page`).style.display = 'block';
  });
});

// 語言切換功能
document.getElementById('language-select').addEventListener('change', function() {
  const lang = this.value;
  console.log('切換語言到:', lang);
  
  // 這裡可以添加實際的語言切換邏輯
  if(lang === 'en') {
    document.documentElement.lang = 'en';
    // 更新所有文字為英文...
  } else {
    document.documentElement.lang = 'zh-TW';
    // 更新所有文字為繁體中文...
  }
});

// 初始化粒子效果（無互動性）
document.addEventListener('DOMContentLoaded', function() {
  if(typeof particlesJS !== 'undefined') {
    particlesJS('particles-js', {
      "particles": {
        "number": { "value": 80 },
        "color": { "value": "#3a86ff" },
        "shape": { "type": "circle" },
        "opacity": { "value": 0.5 },
        "size": { "value": 3, "random": true },
        "line_linked": { 
          "enable": true, 
          "distance": 150, 
          "color": "#3a86ff", 
          "opacity": 0.4, 
          "width": 1 
        },
        "move": { 
          "enable": true, 
          "speed": 2,
          "direction": "none",
          "random": true,
          "straight": false,
          "out_mode": "out" 
        }
      },
      "interactivity": {  // 關閉所有互動
        "detect_on": "canvas",
        "events": {
          "onhover": { "enable": false },
          "onclick": { "enable": false },
          "resize": true
        }
      }
    });
  }
});