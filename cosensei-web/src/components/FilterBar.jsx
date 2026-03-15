import React from 'react'

function FilterBar({ selectedSeverity, onFilterChange, searchTerm, onSearchChange }) {
  return (
    <div style={{ marginBottom: '30px' }}>
      <div className="filter-section">
        <button 
          className={`filter-btn ${selectedSeverity === null ? 'active' : ''}`}
          onClick={() => onFilterChange(null)}
        >
          All Issues ({selectedSeverity === null ? '22' : ''})
        </button>
        <button 
          className={`filter-btn ${selectedSeverity === 'CRITICAL' ? 'active' : ''}`}
          onClick={() => onFilterChange('CRITICAL')}
          style={{
            borderColor: selectedSeverity === 'CRITICAL' ? '#ff4336' : 'rgba(255, 67, 54, 0.3)',
            background: selectedSeverity === 'CRITICAL' ? 'rgba(255, 67, 54, 0.2)' : 'transparent',
            color: selectedSeverity === 'CRITICAL' ? '#ff4336' : '#ff6b6b'
          }}
        >
          🔴 CRITICAL (10)
        </button>
        <button 
          className={`filter-btn ${selectedSeverity === 'HIGH' ? 'active' : ''}`}
          onClick={() => onFilterChange('HIGH')}
          style={{
            borderColor: selectedSeverity === 'HIGH' ? '#ffa500' : 'rgba(255, 152, 0, 0.3)',
            background: selectedSeverity === 'HIGH' ? 'rgba(255, 152, 0, 0.2)' : 'transparent',
            color: selectedSeverity === 'HIGH' ? '#ffa500' : '#ffb74d'
          }}
        >
          🟠 HIGH (9)
        </button>
        <button 
          className={`filter-btn ${selectedSeverity === 'MEDIUM' ? 'active' : ''}`}
          onClick={() => onFilterChange('MEDIUM')}
          style={{
            borderColor: selectedSeverity === 'MEDIUM' ? '#ffc107' : 'rgba(255, 193, 7, 0.3)',
            background: selectedSeverity === 'MEDIUM' ? 'rgba(255, 193, 7, 0.2)' : 'transparent',
            color: selectedSeverity === 'MEDIUM' ? '#ffc107' : '#ffd54f'
          }}
        >
          🟡 MEDIUM (3)
        </button>
      </div>

      <input 
        type="text"
        className="search-box"
        placeholder="🔍 Search vulnerabilities..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
      />
    </div>
  )
}

export default FilterBar
