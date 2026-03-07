import React from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Space } from 'antd';
import { UserOutlined, LogoutOutlined, DashboardOutlined, 
         FileTextOutlined, BulbOutlined, TeamOutlined } from '@ant-design/icons';
import { useAuth } from './hooks/useAuth';
import Login from './pages/Login';
import Register from './pages/Register';
import CandidateDashboard from './pages/candidate/Dashboard';
import ResumeUpload from './pages/candidate/ResumeUpload';
import JobRecommendations from './pages/candidate/JobRecommendations';
import SkillGap from './pages/candidate/SkillGap';
import HRDashboard from './pages/hr/Dashboard';
import JobPost from './pages/hr/JobPost';
import CandidateRanking from './pages/hr/CandidateRanking';
import './App.css';

const { Header, Sider, Content } = Layout;

function App() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const isHR = user?.role === 'hr';

  const candidateMenuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: 'resume',
      icon: <FileTextOutlined />,
      label: 'Resume Upload',
    },
    {
      key: 'jobs',
      icon: <BulbOutlined />,
      label: 'Job Recommendations',
    },
    {
      key: 'skills',
      icon: <TeamOutlined />,
      label: 'Skill Gap Analysis',
    },
  ];

  const hrMenuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: 'jobs',
      icon: <FileTextOutlined />,
      label: 'Job Management',
    },
    {
      key: 'candidates',
      icon: <TeamOutlined />,
      label: 'Candidate Ranking',
    },
  ];

  const userMenu = (
    <Menu>
      <Menu.Item key="profile" icon={<UserOutlined />}>
        Profile
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={logout}>
        Logout
      </Menu.Item>
    </Menu>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        theme="light"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div className="logo" style={{ padding: '16px', textAlign: 'center' }}>
          <h3 style={{ margin: 0, color: '#1890ff' }}>Resume Analyzer</h3>
        </div>
        <Menu
          mode="inline"
          defaultSelectedKeys={['dashboard']}
          items={isHR ? hrMenuItems : candidateMenuItems}
          onClick={({ key }) => {
            if (isHR) {
              switch(key) {
                case 'dashboard':
                  navigate('/hr/dashboard');
                  break;
                case 'jobs':
                  navigate('/hr/job-post');
                  break;
                case 'candidates':
                  navigate('/hr/candidate-ranking');
                  break;
              }
            } else {
              switch(key) {
                case 'dashboard':
                  navigate('/candidate/dashboard');
                  break;
                case 'resume':
                  navigate('/candidate/resume-upload');
                  break;
                case 'jobs':
                  navigate('/candidate/jobs');
                  break;
                case 'skills':
                  navigate('/candidate/skills');
                  break;
              }
            }
          }}
        />
      </Sider>
      <Layout style={{ marginLeft: 200 }}>
        <Header style={{ padding: '0 16px', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0 }}>
              {isHR ? 'HR Dashboard' : 'Candidate Dashboard'}
            </h2>
          </div>
          <Space>
            <span>Welcome, {user?.first_name}!</span>
            <Dropdown overlay={userMenu} placement="bottomRight">
              <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: '16px', overflow: 'initial' }}>
          <Routes>
            {/* Candidate Routes */}
            <Route path="/candidate/dashboard" element={<CandidateDashboard />} />
            <Route path="/candidate/resume-upload" element={<ResumeUpload />} />
            <Route path="/candidate/jobs" element={<JobRecommendations />} />
            <Route path="/candidate/skills" element={<SkillGap />} />
            
            {/* HR Routes */}
            <Route path="/hr/dashboard" element={<HRDashboard />} />
            <Route path="/hr/job-post" element={<JobPost />} />
            <Route path="/hr/candidate-ranking" element={<CandidateRanking />} />
            
            {/* Default redirect */}
            <Route 
              path="*" 
              element={<Navigate to={isHR ? "/hr/dashboard" : "/candidate/dashboard"} replace />} 
            />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;