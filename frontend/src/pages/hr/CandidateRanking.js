import React, { useState } from 'react';
import { 
  Card, Typography, Table, Select, Button, Tag, Space, 
  Progress, Modal, Form, Input, message, Row, Col, Statistic 
} from 'antd';
import { 
  TeamOutlined, 
  EyeOutlined, 
  MailOutlined,
  FilterOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { jobsAPI, applicationsAPI } from '../../services/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const CandidateRanking = () => {
  const [selectedJob, setSelectedJob] = useState(null);
  const [threshold, setThreshold] = useState(30);
  const [statusModalVisible, setStatusModalVisible] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [statusForm] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch HR's posted jobs
  const { data: postedJobs } = useQuery(
    'my-posted-jobs',
    jobsAPI.getMyPostedJobs,
    {
      select: (response) => {
        const data = response?.data;
        if (Array.isArray(data?.results)) {
          return data.results;
        }
        if (Array.isArray(data)) {
          return data;
        }
        return [];
      },
    }
  );

  // Fetch ranked candidates for selected job
  const { data: candidates, isLoading, refetch, error } = useQuery(
    ['ranked-candidates', selectedJob, threshold],
    () => {
      if (!selectedJob) return { data: { candidates: [] } };
      console.log('Fetching candidates for job:', selectedJob, 'threshold:', threshold);
      return jobsAPI.rankCandidates(selectedJob, threshold);
    },
    {
      select: (response) => {
        console.log('API Response for job', selectedJob, ':', response);
        const data = response?.data;
        if (Array.isArray(data?.candidates)) {
          console.log('Found candidates array:', data.candidates.length, 'candidates');
          return data.candidates;
        }
        if (Array.isArray(data)) {
          console.log('Found direct array:', data.length, 'candidates');
          return data;
        }
        console.log('No candidates found, returning empty array');
        return [];
      },
      enabled: !!selectedJob,
      onError: (error) => {
        console.error('Failed to fetch candidates for job', selectedJob, ':', error);
        message.error(`Failed to load candidates: ${error.response?.data?.error || error.message || 'Please try again.'}`);
      },
      onSuccess: (data) => {
        console.log('Candidates loaded successfully for job', selectedJob, ':', data.length, 'candidates');
        if (data.length === 0) {
          message.info('No candidates found for this job above the selected threshold.');
        }
      }
    }
  );

  // Status change mutation
  const changeStatusMutation = useMutation(
    ({ applicationId, status, notes }) => applicationsAPI.changeStatus(applicationId, status, notes),
    {
      onSuccess: (response, variables) => {
        message.success('Application status updated successfully!');
        setStatusModalVisible(false);
        statusForm.resetFields();
        
        // Update the candidate in the local cache
        queryClient.setQueryData(['ranked-candidates', selectedJob, threshold], (oldData) => {
          if (!Array.isArray(oldData)) return oldData; // Ensure oldData is an array
          return oldData.map(candidate => 
            candidate.application_id === variables.applicationId 
              ? { ...candidate, status: response.status, hr_notes: response.hr_notes }
              : candidate
          );
        });
        
        // Invalidate to ensure fresh data
        queryClient.invalidateQueries('ranked-candidates');
        queryClient.invalidateQueries('application-statistics');
      },
      onError: (error) => {
        console.error('Status update error:', error);
        message.error(`Failed to update status: ${error.response?.data?.error || error.message || 'Please try again.'}`);
      },
    }
  );

  const handleJobChange = (jobId) => {
    setSelectedJob(jobId);
  };

  const handleThresholdChange = (value) => {
    setThreshold(value);
  };

  const handleStatusChange = (application) => {
    setSelectedApplication(application);
    setStatusModalVisible(true);
    statusForm.setFieldsValue({
      status: application.status,
      notes: application.hr_notes,
    });
  };

  const handleStatusSubmit = async (values) => {
    // Use the application_id if available, otherwise show an error
    const applicationId = selectedApplication.application_id;
    if (!applicationId) {
      message.error('No application found for this candidate. The candidate must apply first.');
      return;
    }
    
    changeStatusMutation.mutate({
      applicationId: applicationId,
      status: values.status,
      notes: values.notes,
    });
  };

  const getMatchScoreColor = (score) => {
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#faad14';
    return '#f5222d';
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

  const columns = [
    {
      title: 'Candidate',
      dataIndex: 'candidate_details',
      key: 'candidate',
      render: (candidate) => (
        <div>
          <Text strong>{candidate?.first_name} {candidate?.last_name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{candidate?.email}</Text>
          {candidate?.phone && (
            <>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>{candidate?.phone}</Text>
            </>
          )}
        </div>
      ),
    },
    {
      title: 'Match Score',
      dataIndex: 'overall_score',
      key: 'match_score',
      render: (score) => (
        <div style={{ textAlign: 'center' }}>
          <div style={{ 
            fontSize: '16px', 
            fontWeight: 'bold', 
            color: getMatchScoreColor(score) 
          }}>
            {score?.toFixed(1)}%
          </div>
          <Progress 
            percent={score} 
            strokeColor={getMatchScoreColor(score)}
            showInfo={false}
            size="small"
            style={{ width: '80px' }}
          />
        </div>
      ),
      sorter: (a, b) => a.overall_score - b.overall_score,
      defaultSortOrder: 'descend',
    },
    {
      title: 'Skills Match',
      dataIndex: 'skills_match_score',
      key: 'skills_match',
      render: (score) => (
        <div style={{ textAlign: 'center' }}>
          <Text style={{ color: getMatchScoreColor(score) }}>
            {score?.toFixed(1)}%
          </Text>
        </div>
      ),
    },
    {
      title: 'Experience',
      dataIndex: 'experience_match_score',
      key: 'experience_match',
      render: (score) => (
        <div style={{ textAlign: 'center' }}>
          <Text style={{ color: getMatchScoreColor(score) }}>
            {score?.toFixed(1)}%
          </Text>
        </div>
      ),
    },
    {
      title: 'Matched Skills',
      dataIndex: 'matched_skills',
      key: 'matched_skills',
      render: (skills) => (
        <div>
          {skills?.slice(0, 3).map((skill, index) => (
            <Tag key={index} size="small" color="green">{skill}</Tag>
          ))}
          {skills?.length > 3 && (
            <Tag size="small">+{skills.length - 3}</Tag>
          )}
        </div>
      ),
    },
    {
      title: 'Missing Skills',
      dataIndex: 'missing_skills',
      key: 'missing_skills',
      render: (skills) => (
        <div>
          {skills?.slice(0, 3).map((skill, index) => (
            <Tag key={index} size="small" color="orange">{skill}</Tag>
          ))}
          {skills?.length > 3 && (
            <Tag size="small">+{skills.length - 3}</Tag>
          )}
        </div>
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
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => handleStatusChange(record)}
          >
            Review
          </Button>
           <Button
              type="link"
              icon={<FileTextOutlined />}
              onClick={() => {
                if (record.resume_file) {
                  window.open(record.resume_file, '_blank');
                } else {
                  message.warning('Resume not available');
                }
              }}
            >
              Resume
            </Button>
        </Space>
      ),
    },
    {
      title: 'Applied',
      dataIndex: 'applied_at',
      key: 'applied_at',
      render: (date) => {
        if (!date) return 'Not Available';
        try {
          return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
          });
        } catch (error) {
          return 'Invalid Date';
        }
      },
    },
  ];

  return (
    <div>
      <div className="page-header">
        <Title level={2}>Candidate Ranking</Title>
        <Text type="secondary">
          AI-powered candidate ranking based on job requirements
        </Text>
      </div>

      <div className="content-wrapper">
        {/* Filters */}
        <Card style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} md={8}>
              <Select
                placeholder="Select Job"
                style={{ width: '100%' }}
                onChange={handleJobChange}
                value={selectedJob}
              >
                {postedJobs?.map((job) => (
                  <Option key={job.id} value={job.id}>
                    {job.title} - {job.company}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} md={8}>
              <Select
                placeholder="Match Threshold"
                style={{ width: '100%' }}
                onChange={handleThresholdChange}
                value={threshold}
              >
                <Option value={10}>10% (All Candidates)</Option>
                <Option value={30}>30% (Low Threshold)</Option>
                <Option value={50}>50% (Medium Threshold)</Option>
                <Option value={70}>70% (High Threshold)</Option>
                <Option value={85}>85% (Very High Threshold)</Option>
              </Select>
            </Col>
            <Col xs={24} md={8}>
              <Button 
                icon={<FilterOutlined />}
                onClick={() => refetch()}
                disabled={!selectedJob}
              >
                Refresh Rankings
              </Button>
            </Col>
          </Row>
        </Card>

        {/* Statistics */}
        {selectedJob && candidates && (
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="Total Candidates"
                  value={candidates?.length || 0}
                  prefix={<TeamOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="Above Threshold"
                  value={candidates?.filter(candidate => candidate.overall_score >= threshold).length || 0}
                  prefix={<EyeOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="Average Match"
                  value={candidates?.reduce((acc, c) => acc + (c.overall_score || 0), 0) / (candidates?.length || 1) || 0}
                  precision={1}
                  suffix="%"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* Candidates Table */}
        <Card>
          {!selectedJob ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <TeamOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
              <Title level={5} type="secondary">Select a Job to View Candidates</Title>
              <Text type="secondary">Choose a job posting to see ranked candidates</Text>
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <FilterOutlined style={{ fontSize: 48, color: '#ff4d4f', marginBottom: 16 }} />
              <Title level={5} type="danger">Error Loading Candidates</Title>
              <Text type="secondary">Failed to load candidates for this job. Please try again.</Text>
              <Button 
                type="primary" 
                onClick={() => refetch()} 
                style={{ marginTop: 16 }}
              >
                Retry
              </Button>
            </div>
          ) : candidates && candidates.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <EyeOutlined style={{ fontSize: 48, color: '#faad14', marginBottom: 16 }} />
              <Title level={5} type="warning">No Candidates Found</Title>
              <Text type="secondary">
                No candidates found for this job above {threshold}% threshold. 
                Try lowering the threshold to see more candidates.
              </Text>
              <Button 
                type="primary" 
                onClick={() => setThreshold(10)} 
                style={{ marginTop: 16 }}
              >
                Show All Candidates (10% threshold)
              </Button>
            </div>
          ) : (
            <Table
              columns={columns}
              dataSource={candidates?.filter(candidate => candidate.overall_score >= threshold) || []}
              loading={isLoading}
              rowKey="id"
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} candidates`,
              }}
              scroll={{ x: 1000 }}
            />
          )}
        </Card>

        {/* Status Change Modal */}
        <Modal
          title={`Review Application - ${selectedApplication?.candidate_details?.first_name} ${selectedApplication?.candidate_details?.last_name}`}
          open={statusModalVisible}
          onCancel={() => setStatusModalVisible(false)}
          footer={null}
          width={800}
        >
          {selectedApplication && (
            <div>
              <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} md={12}>
                  <Card size="small" title="Match Scores">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <Text strong>Overall: </Text>
                        <Text style={{ color: getMatchScoreColor(selectedApplication.overall_score) }}>
                          {selectedApplication.overall_score.toFixed(1)}%
                        </Text>
                      </div>
                      <div>
                        <Text strong>Skills: </Text>
                        <Text>{selectedApplication.skills_match_score.toFixed(1)}%</Text>
                      </div>
                      <div>
                        <Text strong>Experience: </Text>
                        <Text>{selectedApplication.experience_match_score.toFixed(1)}%</Text>
                      </div>
                    </Space>
                  </Card>
                </Col>
                <Col xs={24} md={12}>
                  <Card size="small" title="Skills Analysis">
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>Matched Skills:</Text>
                      <div style={{ marginTop: 4 }}>
                        {selectedApplication.matched_skills?.slice(0, 5).map((skill, index) => (
                          <Tag key={index} size="small" color="green">{skill}</Tag>
                        ))}
                      </div>
                    </div>
                    <div>
                      <Text strong>Missing Skills:</Text>
                      <div style={{ marginTop: 4 }}>
                        {selectedApplication.missing_skills?.slice(0, 5).map((skill, index) => (
                          <Tag key={index} size="small" color="orange">{skill}</Tag>
                        ))}
                      </div>
                    </div>
                  </Card>
                </Col>
              </Row>

              <Form
                form={statusForm}
                layout="vertical"
                onFinish={handleStatusSubmit}
              >
                <Form.Item
                  name="status"
                  label="Application Status"
                  rules={[{ required: true, message: 'Please select status!' }]}
                >
                  <Select>
                    <Option value="pending">Pending</Option>
                    <Option value="reviewed">Reviewed</Option>
                    <Option value="shortlisted">Shortlisted</Option>
                    <Option value="interviewed">Interviewed</Option>
                    <Option value="offered">Offered</Option>
                    <Option value="rejected">Rejected</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="notes"
                  label="HR Notes"
                >
                  <TextArea
                    rows={4}
                    placeholder="Add notes about this candidate..."
                  />
                </Form.Item>

                <Form.Item>
                  <Space>
                    <Button 
                      type="primary" 
                      htmlType="submit"
                      loading={changeStatusMutation.isLoading}
                    >
                      Update Status
                    </Button>
                    <Button onClick={() => setStatusModalVisible(false)}>
                      Cancel
                    </Button>
                    <Button 
                      icon={<MailOutlined />}
                      onClick={() => window.open(`mailto:${selectedApplication.candidate_details?.email}`)}
                    >
                      Contact Candidate
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
          )}
        </Modal>
      </div>
    </div>
  );
};

export default CandidateRanking;