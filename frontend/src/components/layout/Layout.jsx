import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar.jsx';
import Header from './Header.jsx';

/**
 * Layout — shell that wraps every page.
 * Structure:
 *   <div.app-shell>
 *     <Sidebar />
 *     <div.main-area>
 *       <Header />
 *       <main>  ← page content rendered here via <Outlet />
 *     </div>
 *   </div>
 */
function Layout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-area">
        <Header />
        <main className="page-content" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default Layout;
