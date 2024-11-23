import { createContext, useContext, useState, useEffect } from 'react';
import { getNotifications } from '../services/notificationService';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkNotifications = async () => {
      try {
        const data = await getNotifications();
        // Only update if there are new notifications
        setNotifications(prevNotifications => {
          const newNotifications = data.filter(
            newNotif => !prevNotifications.some(
              prevNotif => prevNotif.id === newNotif.id
            )
          );
          return [...prevNotifications, ...newNotifications];
        });
        setError(null);
      } catch (error) {
        if (!error || error.message !== error?.message) {
          setError(error);
        }
        if (process.env.NODE_ENV === 'development') {
          console.warn('Notification service unavailable');
        }
      }
    };

    // Initial check
    checkNotifications();

    // Check for notifications every 30 seconds
    const interval = setInterval(checkNotifications, 300000);
    return () => clearInterval(interval);
  }, []);

  const markAsRead = (notificationId) => {
    setNotifications(prevNotifications =>
      prevNotifications.map(notification =>
        notification.id === notificationId
          ? { ...notification, read: true }
          : notification
      )
    );
  };

  const value = {
    notifications,
    error,
    markAsRead
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};