import React from 'react';
import { Row, Col, Card, Statistic, Typography, List, Tag, Button, Space } from 'antd';
import { 
  FileTextOutlined, 
  BulbOutlined, 
  TrophyOutlined, 
  ClockCircleOutlined,
  RightOutlined
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import { resumeAPI, jobsAPI, applicationsAPI } from '../../services/api';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const CandidateDashboard = () => {
  const navigate = useNavigate();

  // Fetch user's resumes
  const { data: resumes } = useQuery(
    'resumes',
    resumeAPI.getList,
    {
      select: (response) => {
        // Handle paginated response
        const data = response?.data;
        if (Array.isArray(data?.results)) {
          return data.results;
        }
        // Handle direct array response
        if (Array.isArray(data)) {
          return data;
        }
        // Handle case where data is null/undefined
        return [];
      },
    }
  );

  // Fetch job recommendations
  const { data: recommendations } = useQuery(
    'job-recommendations',
    jobsAPI.getRecommendations,
    {
      select: (response) => {
        // Handle paginated response
        const data = response?.data;
        if (Array.isArray(data?.results)) {
          return data.results;
        }
        // Handle direct array response
        if (Array.isArray(data?.recommendations)) {
          return data.recommendations;
        }
        if (Array.isArray(data)) {
          return data;
        }
        return [];
      },
    }
  );

  // Fetch user's applications
  const { data: applications } = useQuery(
    'applications',
    applicationsAPI.getList,
    {
      select: (response) => {
        // Handle paginated response
        const data = response?.data;
        if (Array.isArray(data?.results)) {
          return data.results;
        }
        // Handle direct array response
        if (Array.isArray(data)) {
          return data;
        }
        return [];
      },
    }
  );

  const latestResume = Array.isArray(resumes) ? resumes?.[0] : null;
  const topRecommendations = Array.isArray(recommendations) ? recommendations?.slice(0, 5) : [];
  const recentApplications = Array.isArray(applications) ? applications?.slice(0, 5) : [];

  return (
    <div>
      <div className="page-header">
        <Title level={2}>Candidate Dashboard</Title>
        <Text type="secondary">
          Welcome back! Here's your job search overview.
        </Text>
      </div>

      <div className="content-wrapper">
        {/* Statistics Cards */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Uploaded Resumes"
                value={resumes?.length || 0}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Job Recommendations"
                value={recommendations?.length || 0}
                prefix={<BulbOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Applications Sent"
                value={applications?.length || 0}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Profile Completion"
                value={latestResume ? 85 : 0}
                suffix="%"
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          {/* Latest Resume Status */}
          <Col xs={24} lg={12}>
            <Card 
              title="Latest Resume" 
              extra={
                <Button 
                  type="link" 
                  onClick={() => navigate('/candidate/resume-upload')}
                >
                  Upload New
                </Button>
              }
            >
              {latestResume ? (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <Title level={5}>{latestResume.title}</Title>
                    <Text type="secondary">
                      Uploaded: {new Date(latestResume.created_at).toLocaleDateString()}
                    </Text>
                  </div>
                  
                  <div style={{ marginBottom: 16 }}>
                    <Tag color={latestResume.processing_status === 'completed' ? 'green' : 'orange'}>
                      {latestResume.processing_status}
                    </Tag>
                    {latestResume.analysis && (
                      <Tag color="blue">
                        Score: {latestResume.analysis.overall_score.toFixed(1)}%
                      </Tag>
                    )}
                  </div>

                  {latestResume.extracted_skills && latestResume.extracted_skills.length > 0 && (
                    <div>
                      <Text strong>Skills: </Text>
                      <div style={{ marginTop: 8 }}>
                        {latestResume.extracted_skills.slice(0, 8).map((skill, index) => (
                          <Tag key={index} className="skill-chip">
                            {skill}
                          </Tag>
                        ))}
                        {latestResume.extracted_skills.length > 8 && (
                          <Tag>+{latestResume.extracted_skills.length - 8} more</Tag>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <FileTextOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                  <Title level={5} type="secondary">No Resume Uploaded</Title>
                  <Text type="secondary">Upload your resume to get started</Text>
                  <div style={{ marginTop: 16 }}>
                    <Button type="primary" onClick={() => navigate('/candidate/resume-upload')}>
                      Upload Resume
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </Col>

          {/* Top Job Recommendations */}
          <Col xs={24} lg={12}>
            <Card 
              title="Top Job Recommendations" 
              extra={
                <Button 
                  type="link" 
                  onClick={() => navigate('/candidate/jobs')}
                >
                  View All
                </Button>
              }
            >
              {topRecommendations && topRecommendations.length > 0 ? (
                <List
                  dataSource={topRecommendations}
                  renderItem={(item) => (
                    <List.Item
                      actions={[
                        <Button 
                          type="link" 
                          icon={<RightOutlined />}
                          onClick={() => navigate('/candidate/jobs')}
                        />
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <div>
                            <Text strong>{item.title}</Text>
                            <div style={{ marginTop: 4 }}>
                              <Text type="secondary">
                                {item.company} • {item.location}
                              </Text>
                            </div>
                          </div>
                        }
                        description={
                          <div>
                            <div style={{ 
                              fontWeight: 600,
                              color: item.match_percentage >= 70 
                                ? '#52c41a' 
                                : item.match_percentage >= 50 
                                ? '#faad14' 
                                : '#f5222d'
                            }}>
                              Match: {item.match_percentage?.toFixed(1)}%
                            </div>

                            {item.required_skills && (
                              <div style={{ marginTop: 4 }}>
                                {item.required_skills.slice(0, 3).map((skill, index) => (
                                  <Tag key={index} size="small">{skill}</Tag>
                                ))}
                              </div>
                            )}
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <BulbOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                  <Title level={5} type="secondary">No Recommendations Yet</Title>
                  <Text type="secondary">Upload your resume to get personalized job recommendations</Text>
                </div>
              )}
            </Card>
          </Col>

          {/* Recent Applications */}
          <Col xs={24}>
            <Card 
              title="Recent Applications" 
              extra={
                <Button 
                  type="link" 
                  onClick={() => navigate('/candidate/jobs')}
                >
                  View All Applications
                </Button>
              }
            >
              {recentApplications && recentApplications.length > 0 ? (
                <List
                  dataSource={recentApplications}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        title={
                          <div>
                            <Text strong>{item.job_details.title}</Text>
                            <div style={{ marginTop: 4 }}>
                              <Text type="secondary">{item.job_details.company}</Text>
                            </div>
                          </div>
                        }
                        description={
                          <Space>
                            <Tag color={getStatusColor(item.status)}>
                              {item.status}
                            </Tag>
                            <Text type="secondary">
                              Applied: {new Date(item.applied_at).toLocaleDateString()}
                            </Text>
                            {item.match_score > 0 && (
                              <Text type="secondary">
                                Match Score: {item.match_score.toFixed(1)}%
                              </Text>
                            )}
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <TrophyOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                  <Title level={5} type="secondary">No Applications Yet</Title>
                  <Text type="secondary">Start applying to jobs from your recommendations</Text>
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

const getStatusColor = (status) => {
  const colors = {
    pending: 'orange',
    reviewed: 'blue',
    shortlisted: 'green',
    interviewed: 'purple',
    offered: 'gold',
    rejected: 'red',
    withdrawn: 'gray',
  };
  return colors[status] || 'default';
};

export default CandidateDashboard;