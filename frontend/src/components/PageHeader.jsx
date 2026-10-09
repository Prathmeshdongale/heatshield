import React from 'react';

/**
 * PageHeader — consistent title + description block at the top of every page.
 *
 * Props:
 *   title       {string}  — page heading
 *   description {string}  — optional sub-text
 *   actions     {node}    — optional right-side controls (selects, buttons)
 */
function PageHeader({ title, description, actions }) {
  return (
    <div className="page-header">
      <div className="page-header__left">
        <h1 className="page-header__title">{title}</h1>
        {description && <p className="page-header__desc">{description}</p>}
      </div>
      <div className="page-header__right">
        {actions}
      </div>
    </div>
  );
}

export default PageHeader;
