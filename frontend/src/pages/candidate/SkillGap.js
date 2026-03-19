import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Row, 
  Col, 
  Progress, 
  Button, 
  Space, 
  Empty, 
  Alert,
  Spin,
  List,
  Tag
} from 'antd';
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  BookOutlined, 
  BulbOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import { resumeAPI, jobsAPI } from '../../services/api';

const { Title, Text, Paragraph } = Typography;

const SkillGap = () => {
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [error, setError] = useState(null);
  const [autoAnalyzed, setAutoAnalyzed] = useState(false);
  
  // Fetch user's jobs
  const { data: jobsResponse, isLoading: jobsLoading, error: jobsError } = useQuery(
    'jobs-list',
    () => jobsAPI.getList(),
    {
      select: (response) => {
        console.log('Jobs API Response:', response); // Debug log
        console.log('Response type:', typeof response); // Debug log
        console.log('Is array:', Array.isArray(response)); // Debug log
        
        // Handle different response structures
        if (Array.isArray(response)) {
          console.log('Response is array, returning directly');
          return response;
        }
        if (response?.data && Array.isArray(response.data)) {
          console.log('Response.data is array, returning response.data');
          return response.data;
        }
        if (response?.results && Array.isArray(response.results)) {
          console.log('Response.results is array, returning response.results');
          return response.results;
        }
        if (response?.results?.data && Array.isArray(response.results.data)) {
          console.log('Response.results.data is array, returning response.results.data');
          return response.results.data;
        }
        
        // Check if response.data is an object with array-like structure
        if (response?.data && typeof response.data === 'object') {
          console.log('Response.data is object, checking for array properties');
          // Look for common array property names
          const possibleArrays = ['results', 'jobs', 'data', 'items'];
          for (const prop of possibleArrays) {
            if (response.data[prop] && Array.isArray(response.data[prop])) {
              console.log(`Found array in response.data.${prop}`);
              return response.data[prop];
            }
          }
          
          // If data is an array-like object (has numeric keys)
          const dataKeys = Object.keys(response.data);
          if (dataKeys.length > 0 && !isNaN(dataKeys[0])) {
            console.log('Converting object to array');
            return Object.values(response.data);
          }
        }
        
        console.log('No array found, returning empty array');
        return [];
      }
    }
  );

  // Auto-select first applied job if available
  useEffect(() => {
    if (jobsResponse && jobsResponse.length > 0 && !autoAnalyzed) {
      console.log('All jobs:', jobsResponse); // Debug all jobs
      console.log('Job structure:', jobsResponse[0]); // Debug job structure
      
      // Find first job that has been applied for
      const appliedJob = jobsResponse.find(job => {
        console.log('Checking job:', job.id, job.title, 'status:', job.status, 'applied:', job.applied, 'application_status:', job.application_status);
        return job.status === 'applied' || job.applied === true || job.application_status === 'applied';
      });
      
      if (appliedJob) {
        console.log('Auto-selecting applied job:', appliedJob);
        setSelectedJobId(appliedJob.id);
        setAutoAnalyzed(true);
      } else if (jobsResponse.length > 0) {
        // If no applied jobs, select first available job
        console.log('No applied jobs found, selecting first job:', jobsResponse[0]);
        setSelectedJobId(jobsResponse[0].id);
        setAutoAnalyzed(true);
      }
    }
  }, [jobsResponse, autoAnalyzed]);

  // Debug logs
  console.log('Jobs Loading:', jobsLoading);
  console.log('Jobs Error:', jobsError);
  console.log('Jobs Response:', jobsResponse);

  // Fetch skill gap analysis
  const { 
    data: skillGapData, 
    isLoading: skillGapLoading, 
    error: skillGapError 
  } = useQuery(
    ['skill-gap-analysis', selectedJobId],
    () => {
      console.log('Making skill gap API call for job ID:', selectedJobId);
      return selectedJobId ? resumeAPI.getSkillGapAnalysis(selectedJobId) : null;
    },
    {
      enabled: !!selectedJobId && !error, // Only fetch when job is selected and no validation error
      select: (response) => {
        console.log('Skill gap API response:', response); // Debug response
        return response?.data || {};
      },
      onSuccess: (data) => {
        console.log('Skill gap data loaded:', data); // Debug loaded data
      },
      onError: (error) => {
        console.log('Skill gap API error:', error); // Debug errors
      }
    }
  );

  const getMatchColor = (percentage) => {
    if (percentage >= 80) return '#52c41a';
    if (percentage >= 60) return '#faad14';
    if (percentage >= 40) return '#1890ff';
    return '#f5222d';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: '#f5222d',
      medium: '#fa8c16',
      low: '#52c41a',
    };
    return colors[priority] || '#d9d9d9';
  };

  const handleAnalyze = () => {
    if (!selectedJobId) {
      setError("Please select a job to analyze");
      return;
    }
    setError(null);
    // Analysis will trigger automatically due to selectedJobId dependency
  };

  const downloadReport = () => {
    if (!skillGapData) return;
    
    const report = {
      job_title: skillGapData.job_title,
      resume_title: skillGapData.resume_title,
      match_percentage: skillGapData.match_percentage,
      candidate_skills: skillGapData.candidate_skills,
      required_skills: skillGapData.required_skills,
      missing_skills: skillGapData.missing_skills,
      analysis_summary: skillGapData.analysis_summary,
      generated_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `skill-gap-analysis-${skillGapData.job_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (jobsLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <Text style={{ marginLeft: '16px' }}>Loading available jobs...</Text>
      </div>
    );
  }

  if (jobsError) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Alert
          message="Error Loading Jobs"
          description={jobsError.message || 'Failed to load jobs. Please try refreshing the page.'}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => window.location.reload()}>
              Refresh Page
            </Button>
          }
        />
      </div>
    );
  }

  console.log('Jobs Response:', jobsResponse); // Debug log

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <BookOutlined /> Skill Gap Analysis
          {autoAnalyzed && selectedJobId && (
            <Tag color="green" style={{ marginLeft: '12px', fontSize: '12px' }}>
              Auto-Analyzed
            </Tag>
          )}
        </Title>
        <Text type="secondary">
          Compare your resume skills with job requirements and identify skill gaps
          {autoAnalyzed && selectedJobId && (
            <span style={{ marginLeft: '8px', color: '#52c41a' }}>
              (Analysis automatically triggered for your applied job)
            </span>
          )}
        </Text>
      </div>

      {/* Job Selection */}
      <Card style={{ marginBottom: '24px' }}>
        <Title level={4}>
          <BulbOutlined /> Select Job to Analyze
        </Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            {jobsResponse && jobsResponse.length > 0 ? (
              <>
                <select
                  style={{ 
                    width: '100%', 
                    padding: '8px', 
                    border: `1px solid ${error ? '#f5222d' : '#d9d9d9'}`, 
                    borderRadius: '6px',
                    outline: error ? '2px solid #f5222d' : 'none'
                  }}
                  onChange={(e) => {
                    setSelectedJobId(e.target.value);
                    setError(null); // Clear error when selection changes
                  }}
                  value={selectedJobId || ''}
                >
                  <option value="">Select a job...</option>
                  {jobsResponse?.map(job => (
                    <option key={job.id} value={job.id}>
                      {job.title} - {job.company}
                    </option>
                  ))}
                </select>
                
                {/* Error Message */}
                {error && (
                  <div style={{ 
                    marginTop: '8px', 
                    color: '#f5222d', 
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    {error}
                  </div>
                )}
                
                {/* Analyze Button */}
                <Button 
                  type="primary" 
                  onClick={handleAnalyze}
                  style={{ 
                    marginTop: '12px', 
                    width: '100%',
                    backgroundColor: selectedJobId ? '#1890ff' : '#d9d9d9',
                    borderColor: selectedJobId ? '#1890ff' : '#d9d9d9'
                  }}
                  disabled={!selectedJobId}
                >
                  Analyze Skill Gap
                </Button>
              </>
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                <Text type="secondary">
                  No jobs available. Please check back later or upload a resume to get job recommendations.
                </Text>
              </div>
            )}
          </Col>
        </Row>
      </Card>

      {/* Skill Gap Analysis Results */}
      {selectedJobId && skillGapLoading && (
        <Card style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <Text>Analyzing skill gaps...</Text>
        </Card>
      )}

      {selectedJobId && skillGapError && (
        <Alert
          message="Error loading skill gap analysis"
          description={skillGapError.message}
          type="error"
          style={{ marginBottom: '24px' }}
        />
      )}

      {selectedJobId && skillGapData && (
        <>
          {/* Match Overview */}
          <Card style={{ marginBottom: '24px' }}>
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} md={12}>
                <Title level={4}>
                  <CheckCircleOutlined /> Match Overview
                </Title>
                <Progress
                  type="circle"
                  percent={skillGapData.match_percentage}
                  strokeColor={getMatchColor(skillGapData.match_percentage)}
                  size={120}
                  format={percent => (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                        {percent}%
                      </div>
                      <div style={{ fontSize: '14px', color: '#666' }}>
                        Skills Match
                      </div>
                    </div>
                  )}
                />
              </Col>
              <Col xs={24} md={12}>
                <div>
                  <Title level={5}>Analysis Summary</Title>
                  <Paragraph>
                    <Text strong>Strengths: </Text>
                    {skillGapData.analysis_summary?.strengths}
                  </Paragraph>
                  <Paragraph>
                    <Text strong>Gaps: </Text>
                    <Text type="danger">{skillGapData.analysis_summary?.gaps}</Text>
                  </Paragraph>
                  <Paragraph>
                    <Text strong>Recommendation: </Text>
                    {skillGapData.analysis_summary?.recommendation}
                  </Paragraph>
                </div>
              </Col>
            </Row>
          </Card>

          {/* Skills Comparison */}
          <Row gutter={[16, 16]}>
            {/* Candidate Skills */}
            <Col xs={24} lg={8}>
              <Card 
                title={
                  <span>
                    <CheckCircleOutlined style={{ color: '#52c41a' }} /> 
                    Your Skills ({skillGapData.total_candidate_skills})
                  </span>
                }
                style={{ height: '400px' }}
              >
                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {skillGapData.candidate_skills?.length > 0 ? (
                    <div>
                      {skillGapData.candidate_skills.map((skill, index) => (
                        <Tag 
                          key={index} 
                          color="green" 
                          style={{ margin: '4px 4px 4px 0' }}
                        >
                          {skill}
                        </Tag>
                      ))}
                    </div>
                  ) : (
                    <Empty description="No skills found in resume" />
                  )}
                </div>
              </Card>
            </Col>

            {/* Required Skills */}
            <Col xs={24} lg={8}>
              <Card 
                title={
                  <span>
                    <BookOutlined style={{ color: '#1890ff' }} /> 
                    Required Skills ({skillGapData.total_required_skills})
                  </span>
                }
                style={{ height: '400px' }}
              >
                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {skillGapData.required_skills?.length > 0 ? (
                    <div>
                      {skillGapData.required_skills.map((skill, index) => (
                        <Tag 
                          key={index} 
                          color="blue" 
                          style={{ margin: '4px 4px 4px 0' }}
                        >
                          {skill}
                        </Tag>
                      ))}
                    </div>
                  ) : (
                    <Empty description="No required skills specified" />
                  )}
                </div>
              </Card>
            </Col>

            {/* Missing Skills */}
            <Col xs={24} lg={8}>
              <Card 
                title={
                  <span>
                    <CloseCircleOutlined style={{ color: '#f5222d' }} /> 
                    Missing Skills ({skillGapData.missing_skills?.length || 0})
                  </span>
                }
                style={{ height: '400px' }}
              >
                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {skillGapData.missing_skills?.length > 0 ? (
                    <div>
                      {skillGapData.missing_skills.map((skill, index) => (
                        <Tag 
                          key={index} 
                          color="red" 
                          style={{ 
                            margin: '4px 4px 4px 0',
                            fontWeight: 'bold',
                            border: '2px solid #ff4d4f'
                          }}
                        >
                          {skill}
                        </Tag>
                      ))}
                    </div>
                  ) : (
                    <Empty 
                      description="No missing skills! Great match!" 
                      style={{ color: '#52c41a' }}
                    />
                  )}
                </div>
              </Card>
            </Col>
          </Row>

          {/* Upskilling Suggestions */}
          {skillGapData.missing_skills?.length > 0 && (
            <Card 
              title={
                <span>
                  <BulbOutlined /> 
                  Upskilling Suggestions
                </span>
              }
              extra={
                <Button 
                  type="primary" 
                  icon={<DownloadOutlined />}
                  onClick={downloadReport}
                >
                  Download Report
                </Button>
              }
            >
              <List
                dataSource={skillGapData.upskilling_suggestions}
                renderItem={(suggestion) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <Space>
                          <Tag color={getPriorityColor(suggestion.priority)}>
                            {suggestion.priority.toUpperCase()}
                          </Tag>
                          <Text strong>{suggestion.skill_name}</Text>
                        </Space>
                      }
                      description={
                        <div>
                          <Text type="secondary">
                            Difficulty: {suggestion.difficulty} | 
                            Estimated Time: {suggestion.estimated_time}
                          </Text>
                          <div style={{ marginTop: '8px' }}>
                            <Text strong>Learning Resources:</Text>
                            <div style={{ marginTop: '4px' }}>
                              {suggestion.resources.map((resource, index) => (
                                <Button
                                  key={index}
                                  type="link"
                                  size="small"
                                  href={resource.url}
                                  target="_blank"
                                  style={{ padding: '0 4px' }}
                                >
                                  {resource.name}
                                </Button>
                              ))}
                            </div>
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}
        </>
      )}

      {/* No Job Selected */}
      {!selectedJobId && (
        <Card style={{ textAlign: 'center', padding: '40px' }}>
          <Empty
            description="Please select a job to analyze skill gaps"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </Card>
      )}
    </div>
  );
};

export default SkillGap;
