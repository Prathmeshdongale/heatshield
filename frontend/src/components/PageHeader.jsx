import React from 'react';

/**
 * PageHeader — consistent title + description block used at the top of every page.
 *
 * Props:
 *   title       {string}  — page heading
 *   description {string}  — optional sub-text
 *   badge       {string}  — optional badge text (defaults to "DEMO DATA")
 *   actions     {node}    — optional right-side controls (selects, buttons)
 */
function PageHeader({ title, description, badge = 'DEMO DATA', actions }) {
  return (
    <div className="page-header">
      <div className="page-header__left">
        <h1 className="page-header__title">{title}</h1>
        {description && (
          <p className="page-header__desc">{description}</p>
        )}
      </div>
      <div className="page-header__right">
        {actions}
        {badge && <span className="demo-badge">{badge}</span>}
      </div>
    </div>
  );
}

export default PageHeader;
