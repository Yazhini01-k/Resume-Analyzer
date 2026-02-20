import React from 'react';
import { Row, Col, Card, Statistic, Typography, List, Tag, Button, Space, Table } from 'antd';
import { 
  TeamOutlined, 
  FileTextOutlined, 
  TrophyOutlined, 
  BarChartOutlined,
  RightOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import { jobsAPI, applicationsAPI } from '../../services/api';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const HRDashboard = () => {
  const navigate = useNavigate();

  // Fetch HR's posted jobs
  const { data: postedJobs } = useQuery(
    'my-posted-jobs',
    jobsAPI.getMyPostedJobs,
    {
      select: (data) => data.data,
    }
  );

  // Fetch application statistics
  const { data: stats, isLoading: statsLoading } = useQuery(
    'application-statistics',
    applicationsAPI.getStatistics,
    {
      select: (data) => data.data,
    }
  );

  // Fetch recent applications
  const { data: recentApplications, isLoading: applicationsLoading } = useQuery(
    'recent-applications',
    () => applicationsAPI.getList({ limit: 5 }),
    {
      select: (data) => data.data,
    }
  );

  const recentJobs = postedJobs?.slice(0, 5);

  const applicationColumns = [
    {
      title: 'Candidate',
      dataIndex: 'candidate_details',
      key: 'candidate',
      render: (candidate) => (
        <div>
          <Text strong>{candidate?.first_name} {candidate?.last_name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{candidate?.email}</Text>
        </div>
      ),
    },
    {
      title: 'Position',
      dataIndex: 'job_details',
      key: 'position',
      render: (job) => (
        <div>
          <Text strong>{job?.title}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{job?.company}</Text>
        </div>
      ),
    },
    {
      title: 'Match Score',
      dataIndex: 'match_score',
      key: 'match_score',
      render: (score) => (
        <Tag color={score >= 70 ? 'green' : score >= 50 ? 'orange' : 'red'}>
          {score?.toFixed(1)}%
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status}
        </Tag>
      ),
    },
    {
      title: 'Applied',
      dataIndex: 'applied_at',
      key: 'applied_at',
      render: (date) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button 
          type="link" 
          icon={<EyeOutlined />}
          onClick={() => navigate(`/hr/candidate-ranking`)}
        >
          View
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div className="page-header">
        <Title level={2}>HR Dashboard</Title>
        <Text type="secondary">
          Manage your job postings and track applications
        </Text>
      </div>

      <div className="content-wrapper">
        {/* Statistics Cards */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card loading={statsLoading}>
              <Statistic
                title="Total Applications"
                value={stats?.total_applications || 0}
                prefix={<TeamOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card loading={statsLoading}>
              <Statistic
                title="Pending Review"
                value={stats?.pending_applications || 0}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card loading={statsLoading}>
              <Statistic
                title="Shortlisted"
                value={stats?.shortlisted_applications || 0}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card loading={statsLoading}>
              <Statistic
                title="Avg Match Score"
                value={stats?.average_match_score || 0}
                precision={1}
                suffix="%"
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          {/* Recent Job Postings */}
          <Col xs={24} lg={12}>
            <Card 
              title="Recent Job Postings" 
              extra={
                <Button 
                  type="link" 
                  onClick={() => navigate('/hr/job-post')}
                >
                  Post New Job
                </Button>
              }
            >
              {recentJobs && recentJobs.length > 0 ? (
                <List
                  dataSource={recentJobs}
                  renderItem={(job) => (
                    <List.Item
                      actions={[
                        <Button 
                          type="link" 
                          icon={<RightOutlined />}
                          onClick={() => navigate('/hr/job-post')}
                        />
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <div>
                            <Text strong>{job.title}</Text>
                            <div style={{ marginTop: 4 }}>
                              <Text type="secondary">{job.company}</Text>
                            </div>
                          </div>
                        }
                        description={
                          <Space>
                            <Tag color="blue">{job.job_type}</Tag>
                            <Tag>{job.experience_level}</Tag>
                            <Text type="secondary">
                              {job.application_count} applicants
                            </Text>
                            <Text type="secondary">
                              {job.view_count} views
                            </Text>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <FileTextOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                  <Title level={5} type="secondary">No Job Postings</Title>
                  <Text type="secondary">Post your first job to start receiving applications</Text>
                  <div style={{ marginTop: 16 }}>
                    <Button type="primary" onClick={() => navigate('/hr/job-post')}>
                      Post Job
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </Col>

          {/* Application Status Breakdown */}
          <Col xs={24} lg={12}>
            <Card title="Application Status">
              {stats?.status_breakdown && stats.status_breakdown.length > 0 ? (
                <List
                  dataSource={stats.status_breakdown}
                  renderItem={(status) => (
                    <List.Item>
                      <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Space>
                          <Tag color={getStatusColor(status.status)}>
                            {status.status}
                          </Tag>
                          <Text strong>{status.count}</Text>
                        </Space>
                        <Text type="secondary">
                          {stats.total_applications > 0 
                            ? `${((status.count / stats.total_applications) * 100).toFixed(1)}%`
                            : '0%'
                          }
                        </Text>
                      </div>
                    </List.Item>
                  )}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <TeamOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                  <Title level={5} type="secondary">No Applications Yet</Title>
                  <Text type="secondary">Applications will appear here once candidates start applying</Text>
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
                  onClick={() => navigate('/hr/candidate-ranking')}
                >
                  View All Applications
                </Button>
              }
            >
              <Table
                columns={applicationColumns}
                dataSource={recentApplications}
                loading={applicationsLoading}
                pagination={false}
                rowKey="id"
                scroll={{ x: 800 }}
              />
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

export default HRDashboard;
