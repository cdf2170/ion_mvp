# Device Search Persistence Guide

## Problem
When users search for devices and click into a device detail, the search state is lost. When they navigate back, they have to re-enter their search query and filters.

## Solution
Use URL parameters to persist search state across navigation. The backend now supports passing search context to device detail endpoints.

---

## Backend Changes (Already Implemented)

### Enhanced Device Detail Endpoint
```http
GET /v1/devices/{device_id}?search_query=laptop&page=2&compliant=false&device_status=Connected&tags=Remote,VIP
```

**New Parameters:**
- `search_query`: Original search query
- `page`: Original page number  
- `compliant`: Original compliance filter
- `device_status`: Original status filter
- `tags`: Original tags filter

**Response includes search context:**
```json
{
  "id": "device-uuid-1",
  "name": "John's MacBook Pro",
  "owner_name": "John Doe",
  // ... other device fields
  "search_context": {
    "search_query": "laptop",
    "page": 2,
    "compliant": false,
    "status": "Connected",
    "tags": "Remote,VIP"
  }
}
```

---

## Frontend Implementation

### 1. Device List Component - Preserve Search in URLs

```javascript
// DeviceList.jsx
import { useSearchParams, useNavigate } from 'react-router-dom';

const DeviceList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Get current search state from URL
  const searchQuery = searchParams.get('query') || '';
  const page = parseInt(searchParams.get('page')) || 1;
  const compliant = searchParams.get('compliant');
  const status = searchParams.get('status');
  const tags = searchParams.get('tags');
  
  // Update search parameters
  const updateSearch = (newParams) => {
    const updatedParams = new URLSearchParams(searchParams);
    
    Object.entries(newParams).forEach(([key, value]) => {
      if (value === null || value === undefined || value === '') {
        updatedParams.delete(key);
      } else {
        updatedParams.set(key, value);
      }
    });
    
    setSearchParams(updatedParams);
  };
  
  // Navigate to device detail with search context
  const viewDevice = (deviceId) => {
    const searchContext = new URLSearchParams();
    
    if (searchQuery) searchContext.set('search_query', searchQuery);
    if (page > 1) searchContext.set('page', page.toString());
    if (compliant !== null) searchContext.set('compliant', compliant);
    if (status) searchContext.set('device_status', status);
    if (tags) searchContext.set('tags', tags);
    
    navigate(`/devices/${deviceId}?${searchContext.toString()}`);
  };
  
  return (
    <div>
      {/* Search Input */}
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => updateSearch({ query: e.target.value, page: 1 })}
        placeholder="Search devices..."
      />
      
      {/* Filters */}
      <select 
        value={compliant || ''}
        onChange={(e) => updateSearch({ compliant: e.target.value, page: 1 })}
      >
        <option value="">All Compliance</option>
        <option value="true">Compliant</option>
        <option value="false">Non-Compliant</option>
      </select>
      
      {/* Device List */}
      {devices.map(device => (
        <div key={device.id} onClick={() => viewDevice(device.id)}>
          {device.name} - {device.owner_name}
        </div>
      ))}
      
      {/* Pagination */}
      <button 
        onClick={() => updateSearch({ page: page - 1 })}
        disabled={page <= 1}
      >
        Previous
      </button>
      <span>Page {page}</span>
      <button 
        onClick={() => updateSearch({ page: page + 1 })}
        disabled={page >= totalPages}
      >
        Next
      </button>
    </div>
  );
};
```

### 2. Device Detail Component - Back to Search

```javascript
// DeviceDetail.jsx
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';

const DeviceDetail = () => {
  const { deviceId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [device, setDevice] = useState(null);
  
  useEffect(() => {
    const fetchDevice = async () => {
      // Pass search context to backend
      const contextParams = new URLSearchParams();
      
      ['search_query', 'page', 'compliant', 'device_status', 'tags'].forEach(param => {
        const value = searchParams.get(param);
        if (value) contextParams.set(param, value);
      });
      
      const url = `/api/v1/devices/${deviceId}?${contextParams.toString()}`;
      const response = await fetch(url);
      const deviceData = await response.json();
      setDevice(deviceData);
    };
    
    fetchDevice();
  }, [deviceId, searchParams]);
  
  const backToSearch = () => {
    // Use search context from device response or URL params
    const searchContext = device?.search_context || {};
    const backParams = new URLSearchParams();
    
    if (searchContext.search_query) backParams.set('query', searchContext.search_query);
    if (searchContext.page) backParams.set('page', searchContext.page.toString());
    if (searchContext.compliant !== undefined) backParams.set('compliant', searchContext.compliant.toString());
    if (searchContext.status) backParams.set('status', searchContext.status);
    if (searchContext.tags) backParams.set('tags', searchContext.tags);
    
    navigate(`/devices?${backParams.toString()}`);
  };
  
  if (!device) return <div>Loading...</div>;
  
  return (
    <div>
      {/* Back Button with Search Context */}
      <button onClick={backToSearch}>
        ← Back to Search Results
      </button>
      
      {/* Device Details */}
      <h1>{device.name}</h1>
      <p>Owner: {device.owner_name}</p>
      <p>Status: {device.status}</p>
      <p>Compliant: {device.compliant ? 'Yes' : 'No'}</p>
      
      {/* Show search context for debugging */}
      {device.search_context && (
        <div style={{ background: '#f0f0f0', padding: '10px', marginTop: '20px' }}>
          <strong>Search Context:</strong>
          <pre>{JSON.stringify(device.search_context, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
```

### 3. Router Setup

```javascript
// App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/devices" element={<DeviceList />} />
        <Route path="/devices/:deviceId" element={<DeviceDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## Key Benefits

1. **Persistent Search**: Search query and filters are preserved in URL
2. **Bookmarkable**: Users can bookmark search results
3. **Browser Back/Forward**: Works with browser navigation
4. **Multiple Devices**: Can look up multiple devices without re-searching
5. **Context Aware**: Backend knows the search context for analytics

---

## URL Examples

**Device List with Search:**
```
/devices?query=laptop&page=2&compliant=false&status=Connected&tags=Remote
```

**Device Detail with Context:**
```
/devices/123e4567-e89b-12d3-a456-426614174000?search_query=laptop&page=2&compliant=false
```

**Back to Search Results:**
```
/devices?query=laptop&page=2&compliant=false&status=Connected&tags=Remote
```

---

## Testing the Implementation

1. **Search for devices**: Enter "laptop" in search
2. **Apply filters**: Set compliance to "Non-Compliant"
3. **Navigate to page 2**: Click pagination
4. **Click on a device**: Should navigate with context
5. **Click "Back to Search"**: Should return to exact same search state
6. **Verify URL**: Should show all search parameters

The search state is now fully persistent across navigation!
