import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { authApi } from '@/api/authApi';
import { AuthContext } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

export default function Register() {
  const { register, handleSubmit, formState: { errors }, watch } = useForm();
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const password = watch('password');

  const onSubmit = async (data) => {
    setLoading(true);
    setErrorMsg('');
    try {
      // 1. Register the user
      await authApi.register(data.email, data.password, data.fullName);
      
      // 2. Automatically log them in after registration
      const loginResponse = await authApi.login(data.email, data.password);
      login(loginResponse.access_token);
      navigate('/dashboard');
    } catch (err) {
      let message = 'Registration failed. Please try again.';
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail.map(e => e.msg).join(', ');
      }
      setErrorMsg(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-muted/40 px-4 py-8">
      <Card className="w-full max-w-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold tracking-tight">Create an account</CardTitle>
          <CardDescription>Enter your details below to create your account</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            {errorMsg && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                {errorMsg}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="John Doe"
                {...register('fullName', { required: 'Full name is required' })}
              />
              {errors.fullName && <span className="text-xs text-destructive">{errors.fullName.message}</span>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                {...register('email', { 
                  required: 'Email is required',
                  pattern: { value: /\S+@\S+\.\S+/, message: 'Invalid email address' }
                })}
              />
              {errors.email && <span className="text-xs text-destructive">{errors.email.message}</span>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                {...register('password', { 
                  required: 'Password is required',
                  minLength: { value: 8, message: 'Password must be at least 8 characters' }
                })}
              />
              {errors.password && <span className="text-xs text-destructive">{errors.password.message}</span>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                {...register('confirmPassword', { 
                  required: 'Please confirm your password',
                  validate: value => value === password || 'Passwords do not match'
                })}
              />
              {errors.confirmPassword && <span className="text-xs text-destructive">{errors.confirmPassword.message}</span>}
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button className="w-full" type="submit" disabled={loading}>
              {loading ? 'Creating account...' : 'Create account'}
            </Button>
            <div className="text-center text-sm">
              Already have an account?{' '}
              <Link to="/login" className="underline hover:text-primary">
                Login
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
