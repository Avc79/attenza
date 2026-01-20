// Main App Logic

const API = {
    getHeaders: () => {
        const token = localStorage.getItem('token');
        return {
            'Authorization': `Bearer ${token}`
        };
    },
    
    checkAuth: () => {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return false;
        }
        return true;
    },
    
    getUser: async () => {
        try {
            const response = await fetch('/users/me', {
                headers: API.getHeaders()
            });
            if (!response.ok) throw new Error('Unauthorized');
            return await response.json();
        } catch (e) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    }
};

// Global shared state or utility functions can go here
