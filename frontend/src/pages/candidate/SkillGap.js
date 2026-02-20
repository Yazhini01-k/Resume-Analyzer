import React from 'react';
import { Card, Typography, List, Tag, Progress, Button, Space, Empty, Row, Col } from 'antd';
import { 
  BulbOutlined, 
  BookOutlined, 
  ClockCircleOutlined,
  TrophyOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import { mlAPI } from '../../services/api';

const { Title, Text, Paragraph } = Typography;

const SkillGap = () => {
  // Fetch upskilling suggestions
  const { data: suggestions, isLoading } = useQuery(
    'upskilling-suggestions',
    mlAPI.getUpskillingSuggestions,
    {
      select: (response) =>
        Array.isArray(response?.data?.results)
          ? response.data.results
          : response?.data || [],
    }
  );

  const getPriorityColor = (score) => {
    if (score >= 80) return '#f5222d';
    if (score >= 60) return '#fa8c16';
    if (score >= 40) return '#1890ff';
    return '#52c41a';
  };

  const getDifficultyColor = (difficulty) => {
    const colors = {
      beginner: '#52c41a',
      intermediate: '#1890ff',
      advanced: '#722ed1',
    };
    return colors[difficulty] || '#d9d9d9';
  };

  const getCompletionStatus = (suggestion) => {
    if (suggestion.is_completed) return 'completed';
    if (suggestion.completion_percentage > 0) return 'in-progress';
    return 'not-started';
  };

  return (
    <div>
      <div className="page-header">
        <Title level={2}>Skill Gap Analysis</Title>
        <Text type="secondary">
          Identify and improve skills needed for your target jobs
        </Text>
      </div>

      <div className="content-wrapper">
        {isLoading ? (
          <div className="loading-container">
            Loading skill analysis...
          </div>
        ) : !suggestions || suggestions.length === 0 ? (
          <Empty
            description="No skill gap analysis available"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" href="/candidate/resume-upload">
              Upload Resume First
            </Button>
          </Empty>
        ) : (
          <Row gutter={[16, 16]}>
            {/* Overview Stats */}
            <Col xs={24} lg={8}>
              <Card title="Learning Overview">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Title level={4}>
                      {suggestions.filter(s => s.is_completed).length}
                    </Title>
                    <Text type="secondary">Skills Completed</Text>
                  </div>
                  <div>
                    <Title level={4}>
                      {suggestions.filter(s => s.completion_percentage > 0 && !s.is_completed).length}
                    </Title>
                    <Text type="secondary">In Progress</Text>
                  </div>
                  <div>
                    <Title level={4}>
                      {suggestions.filter(s => s.completion_percentage === 0).length}
                    </Title>
                    <Text type="secondary">Not Started</Text>
                  </div>
                  <div>
                    <Title level={4}>
                      {Math.round(suggestions.reduce((acc, s) => acc + s.completion_percentage, 0) / suggestions.length)}%
                    </Title>
                    <Text type="secondary">Overall Progress</Text>
                  </div>
                </Space>
              </Card>
            </Col>

            {/* Skill Suggestions */}
            <Col xs={24} lg={16}>
              <Card title="Recommended Skills to Learn">
                <List
                  dataSource={suggestions}
                  renderItem={(suggestion) => {
                    const status = getCompletionStatus(suggestion);
                    return (
                      <List.Item>
                        <Card size="small" className="skill-gap-item">
                          <Row gutter={[16, 16]}>
                            <Col xs={24} md={12}>
                              <div>
                                <Title level={5} style={{ marginBottom: 8 }}>
                                  {suggestion.skill_name}
                                  {status === 'completed' && (
                                    <CheckCircleOutlined 
                                      style={{ color: '#52c41a', marginLeft: 8 }} 
                                    />
                                  )}
                                </Title>
                                
                                <Space wrap style={{ marginBottom: 8 }}>
                                  <Tag color={getDifficultyColor(suggestion.difficulty_level)}>
                                    {suggestion.difficulty_level}
                                  </Tag>
                                  <Tag color={getPriorityColor(suggestion.priority_score)}>
                                    Priority: {suggestion.priority_score.toFixed(0)}
                                  </Tag>
                                  <Tag icon={<ClockCircleOutlined />}>
                                    {suggestion.estimated_time_hours}h
                                  </Tag>
                                </Space>

                                <Paragraph type="secondary" style={{ marginBottom: 12 }}>
                                  Current: {suggestion.current_level} → Target: {suggestion.target_level}
                                </Paragraph>

                                {status !== 'completed' && (
                                  <div style={{ marginBottom: 12 }}>
                                    <Text strong>Progress: </Text>
                                    <Progress 
                                      percent={suggestion.completion_percentage} 
                                      size="small"
                                      style={{ width: '200px', marginLeft: 8 }}
                                    />
                                  </div>
                                )}

                                <Space>
                                  {status === 'not-started' && (
                                    <Button type="primary" size="small">
                                      Start Learning
                                    </Button>
                                  )}
                                  {status === 'in-progress' && (
                                    <Button size="small">
                                      Continue Learning
                                    </Button>
                                  )}
                                  {status === 'completed' && (
                                    <Tag color="success">Completed</Tag>
                                  )}
                                </Space>
                              </div>
                            </Col>

                            <Col xs={24} md={12}>
                              <div>
                                <Title level={5}>
                                  <BookOutlined style={{ marginRight: 8 }} />
                                  Learning Resources
                                </Title>
                                
                                {suggestion.learning_resources && suggestion.learning_resources.length > 0 ? (
                                  <List
                                    size="small"
                                    dataSource={suggestion.learning_resources}
                                    renderItem={(resource) => (
                                      <List.Item>
                                        <div style={{ width: '100%' }}>
                                          <div style={{ fontWeight: 500 }}>
                                            {resource.title}
                                          </div>
                                          <Space>
                                            <Tag size="small">{resource.type}</Tag>
                                            <Text type="secondary">{resource.provider}</Text>
                                            <Text type="secondary">{resource.duration}</Text>
                                            {resource.rating && (
                                              <Text type="secondary">⭐ {resource.rating}</Text>
                                            )}
                                          </Space>
                                        </div>
                                      </List.Item>
                                    )}
                                  />
                                ) : (
                                  <Text type="secondary">No resources available</Text>
                                )}
                              </div>
                            </Col>
                          </Row>
                        </Card>
                      </List.Item>
                    );
                  }}
                />
              </Card>
            </Col>

            {/* Learning Tips */}
            <Col xs={24}>
              <Card title="Learning Tips & Best Practices">
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={8}>
                    <Card size="small">
                      <BulbOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
                      <Title level={5}>Start with High Priority</Title>
                      <Paragraph type="secondary">
                        Focus on skills with the highest priority scores first, as these are most in-demand for your target jobs.
                      </Paragraph>
                    </Card>
                  </Col>
                  <Col xs={24} md={8}>
                    <Card size="small">
                      <TrophyOutlined style={{ fontSize: 24, color: '#52c41a', marginBottom: 8 }} />
                      <Title level={5}>Track Your Progress</Title>
                      <Paragraph type="secondary">
                        Update your progress regularly to see how you're improving and stay motivated.
                      </Paragraph>
                    </Card>
                  </Col>
                  <Col xs={24} md={8}>
                    <Card size="small">
                      <BookOutlined style={{ fontSize: 24, color: '#722ed1', marginBottom: 8 }} />
                      <Title level={5}>Use Multiple Resources</Title>
                      <Paragraph type="secondary">
                        Combine different learning materials like courses, tutorials, and projects for better understanding.
                      </Paragraph>
                    </Card>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        )}
      </div>
    </div>
  );
};

export default SkillGap;
