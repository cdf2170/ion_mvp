# Tag Filtering Frontend Integration Guide

##  **Tag Filtering Issue & Solution**

### **The Problem You're Experiencing:**
When you click "Remote" in the dropdown, it shows ALL devices (Remote, On-Site, BYOD, Corporate, SLT, etc.) instead of filtering to show ONLY Remote devices.

### **Root Cause:**
The frontend dropdown is displaying all available tag options instead of applying the filter to the API request.

---

##  **Correct Frontend Implementation**

### **1. Tag Filtering API Usage**

The backend API supports tag filtering correctly. Here's how to use it:

#### **Single Tag Filter:**
```javascript
// Get only devices with "Remote" tag
const response = await fetch('/v1/devices?tags=Remote', {
  headers: {
    'Authorization': 'Bearer token 21700',
    'Content-Type': 'application/json'
  }
});
```

#### **Multiple Tag Filter (OR Logic):**
```javascript
// Get devices that have EITHER "Remote" OR "On-Site" tags
const response = await fetch('/v1/devices?tags=Remote,On-Site', {
  headers: {
    'Authorization': 'Bearer token 21700',
    'Content-Type': 'application/json'
  }
});
```

#### **Combined Filters:**
```javascript
// Get Remote devices that are compliant and connected
const response = await fetch('/v1/devices?tags=Remote&compliant=true&status=Connected', {
  headers: {
    'Authorization': 'Bearer token 21700',
    'Content-Type': 'application/json'
  }
});
```

---

## 🔧 **Frontend Dropdown Implementation**

### **Correct Dropdown Behavior:**

```javascript
//  WRONG: Shows all devices regardless of selection
function handleTagSelect(selectedTag) {
  // This is wrong - it's not filtering
  fetchAllDevices(); // Shows everything
}

//  CORRECT: Filters devices based on selection
function handleTagSelect(selectedTag) {
  if (selectedTag === 'all') {
    // Show all devices
    fetchDevices();
  } else {
    // Filter by selected tag
    fetchDevices(`?tags=${selectedTag}`);
  }
}

async function fetchDevices(filterParams = '') {
  const response = await fetch(`/v1/devices${filterParams}`, {
    headers: {
      'Authorization': 'Bearer token 21700',
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  updateDeviceList(data.devices); // Update UI with filtered results
}
```

### **Dropdown Component Example:**

```javascript
function TagFilterDropdown({ onTagSelect, currentTag }) {
  const availableTags = [
    'all', 'BYOD', 'Remote', 'On-Site', 'Corporate', 
    'Executive', 'VIP', 'SLT', 'Production', 'Testing'
  ];

  return (
    <select 
      value={currentTag} 
      onChange={(e) => onTagSelect(e.target.value)}
    >
      <option value="all">All Tags</option>
      {availableTags.map(tag => (
        <option key={tag} value={tag}>{tag}</option>
      ))}
    </select>
  );
}
```

---

## 🧪 **Testing Tag Filtering**

### **Test Commands:**

```bash
# Test single tag filter
curl -H "Authorization: Bearer token 21700" \
  "https://api.privion.tech/v1/devices?tags=Remote"

# Test multiple tag filter
curl -H "Authorization: Bearer token 21700" \
  "https://api.privion.tech/v1/devices?tags=Remote,On-Site"

# Test non-existent tag (should return 0 devices)
curl -H "Authorization: Bearer token 21700" \
  "https://api.privion.tech/v1/devices?tags=nonexistent"
```

### **Expected Results:**

- **`?tags=Remote`** → Only devices with "Remote" tag
- **`?tags=BYOD`** → Only devices with "BYOD" tag  
- **`?tags=Remote,On-Site`** → Devices with EITHER "Remote" OR "On-Site" tags
- **`?tags=nonexistent`** → 0 devices (correctly filtered out)

---

##  **Available Tags in Your System**

Based on the seeded data, these tags are available:

- **BYOD** - Bring Your Own Device
- **Remote** - Remote work devices
- **On-Site** - On-site work devices
- **Corporate** - Corporate devices
- **Executive** - Executive devices
- **VIP** - VIP devices
- **SLT** - Senior Leadership Team
- **Production** - Production environment
- **Testing** - Testing environment
- **Contract** - Contract workers
- **Full-Time** - Full-time employees

---

##  **Frontend Fix Checklist**

### **What to Check in Your Frontend:**

1. ** Dropdown Selection Handler:**
   - Does clicking "Remote" call the API with `?tags=Remote`?
   - Or does it just show all devices?

2. ** API Request:**
   - Are you adding the `tags` parameter to the URL?
   - Are you using the correct API endpoint?

3. ** State Management:**
   - Are you updating the device list with filtered results?
   - Or are you showing the same unfiltered list?

4. ** URL Parameters:**
   - Check browser dev tools Network tab
   - Verify the actual API request includes the tag filter

### **Quick Debug Steps:**

1. **Open Browser Dev Tools → Network Tab**
2. **Click "Remote" in your dropdown**
3. **Check the API request URL:**
   -  Should be: `/v1/devices?tags=Remote`
   -  Wrong: `/v1/devices` (no filter)

4. **Check the response:**
   -  Should return only devices with "Remote" tag
   -  Wrong: Returns all devices

---

##  **Backend is Working Perfectly**

The backend API tag filtering is working correctly:

-  Single tag filtering works
-  Multiple tag filtering (OR logic) works  
-  Case-insensitive matching works
-  Non-existent tags return 0 results
-  Works on both local (port 8001) and Railway

**The issue is in the frontend implementation, not the backend API.**

---

##  **Need Help?**

If you're still having issues after implementing the correct frontend logic, check:

1. **Network Tab** - What URL is actually being called?
2. **Console Logs** - Any JavaScript errors?
3. **API Response** - What data is being returned?
4. **State Updates** - Is the UI updating with filtered results?

The backend is ready and working - it's just a matter of connecting the frontend dropdown to the API correctly! 
