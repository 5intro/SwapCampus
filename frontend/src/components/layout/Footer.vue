<template>
  <footer class="app-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="footer-icon">&#127795;</span>
        <span class="footer-title">SwapCampus</span>
        <p class="footer-desc">北京林业大学 · 校园闲置物品交易平台</p>
      </div>
      <div class="footer-links">
        <span>让闲置流转，让信任传递</span>
        <span class="footer-divider">|</span>
        <span>软件工程（课程设计）T-02</span>
      </div>
      <div class="footer-copy">
        &copy; {{ new Date().getFullYear() }} SwapCampus Team. MIT License.
      </div>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  margin-top: 60px;
  padding: 32px 20px 24px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 13px;
}

.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.footer-icon {
  font-size: 20px;
}

.footer-title {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 16px;
}

.footer-desc {
  color: var(--text-secondary);
  margin: 0;
  width: 100%;
}

.footer-links {
  display: flex;
  gap: 8px;
  align-items: center;
}

.footer-divider {
  color: var(--border-color);
}

.footer-copy {
  width: 100%;
  text-align: center;
  padding-top: 8px;
}

@media (max-width: 640px) {
  .footer-inner {
    flex-direction: column;
    text-align: center;
  }
}
</style>
