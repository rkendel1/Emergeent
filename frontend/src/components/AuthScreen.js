import React, { useState } from 'react';
import Login from './Login';
import Signup from './Signup';

const AuthScreen = () => {
  const [isLogin, setIsLogin] = useState(true);

  const toggleMode = () => {
    setIsLogin(!isLogin);
  };

  return isLogin ? (
    <Login onToggleMode={toggleMode} />
  ) : (
    <Signup onToggleMode={toggleMode} />
  );
};

export default AuthScreen;