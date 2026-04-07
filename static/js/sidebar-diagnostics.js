<!--
Sidebar Mobile Troubleshooting Checklist
Add this to your browser console to diagnose sidebar issues
-->

<script>
  // Check viewport width
  console.log('📱 Viewport width:', window.innerWidth + 'px');
  console.log('Mobile check (≤768px):', window.innerWidth <= 768);

  // Check for sidebar element
  const sidebar = document.getElementById('sidebar');
  console.log('✓ Sidebar element found:', !!sidebar);

  if (sidebar) {
    console.log('  - Classes:', sidebar.className);
    console.log('  - Display:', getComputedStyle(sidebar).display);
    console.log('  - Position:', getComputedStyle(sidebar).position);
    console.log('  - Left value:', getComputedStyle(sidebar).left);
    console.log('  - Z-index:', getComputedStyle(sidebar).zIndex);
    console.log('  - Width:', getComputedStyle(sidebar).width);
    console.log('  - Visibility:', getComputedStyle(sidebar).visibility);
    console.log('  - Opacity:', getComputedStyle(sidebar).opacity);
  }

  // Check for toggle button
  const toggle = document.getElementById('sidebar-toggle');
  console.log('✓ Toggle button found:', !!toggle);
  if (toggle) {
    console.log('  - Display:', getComputedStyle(toggle).display);
    console.log('  - Visible:', getComputedStyle(toggle).display !== 'none');
  }

  // Check for overlay
  const overlay = document.getElementById('sidebar-overlay');
  console.log('✓ Overlay element found:', !!overlay);
  if (overlay) {
    console.log('  - Display:', getComputedStyle(overlay).display);
    console.log('  - Position:', getComputedStyle(overlay).position);
    console.log('  - Z-index:', getComputedStyle(overlay).zIndex);
  }

  // Check for SidebarManager
  console.log('✓ SidebarManager loaded:', !!window.sidebarManager);
  if (window.sidebarManager) {
    console.log('  - Sidebar ref:', !!window.sidebarManager.sidebar);
    console.log('  - Toggle ref:', !!window.sidebarManager.sidebarToggle);
    console.log('  - Overlay ref:', !!window.sidebarManager.sidebarOverlay);
  }

  // Test toggle functionality
  console.log('\n📋 Testing sidebar toggle...');
  console.log('Before toggle - sidebar.classList:', sidebar?.className);

  // Manual test commands:
  console.log('\n💡 Test commands:');
  console.log('1. Toggle sidebar: sidebar.classList.toggle("open")');
  console.log('2. Open sidebar: document.getElementById("sidebar").classList.add("open")');
  console.log('3. Close sidebar: document.getElementById("sidebar").classList.remove("open")');
  console.log('4. Trigger toggle button: document.getElementById("sidebar-toggle").click()');
  console.log('5. Check toggle event: window.sidebarManager?.toggleSidebar()');
</script>
