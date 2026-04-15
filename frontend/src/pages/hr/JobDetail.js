import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Card, Typography, Tag, Space, Button, message, Modal } from 'antd';
import { jobsAPI } from '../../services/api';

const { Title, Text } = Typography;

const JobDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Fetch job
  const { data: job } = useQuery(
    ['job-detail', id],
    () => jobsAPI.getDetail(id),
    {
      select: (res) => res?.data,
    }
  );

  // Close Job Mutation
  const closeJobMutation = useMutation(
    (data) => jobsAPI.update(id, data),
    {
      onSuccess: () => {
        message.success('Job closed successfully');
        queryClient.invalidateQueries('my-posted-jobs');
        navigate('/hr/job-management');
      },
      onError: () => {
        message.error('Failed to close job');
      }
    }
  );

  if (!job) return <div>Loading...</div>;

  return (
    <div style={{ padding: 24 }}>
      <Card>

        {/* ✅ BACK BUTTON */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <Button 
              type="primary"
              onClick={() => navigate('/hr/job-management')}
            >
              ← Back
            </Button>
          </div>

        {/* HEADER */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>

          <div>
            <Title level={2}>{job.title}</Title>

            <Space style={{ marginBottom: 12 }}>
              <Tag color="blue">{job.company}</Tag>
              <Tag color="green">{job.job_type}</Tag>
              <Tag>{job.experience_level}</Tag>

              {/* STATUS */}
              <Tag color={job.is_active ? 'green' : 'orange'}>
                {job.is_active ? 'active' : 'closed'}
              </Tag>
            </Space>
          </div>

          {/* ✅ ACTION BUTTONS */}
          {job.is_active && (
            <Space>
              <Button onClick={() => navigate(`/hr/job-post/${job.id}`)}>
                Edit
              </Button>

              <Button
                danger
                loading={closeJobMutation.isLoading}
                onClick={() => {
                  Modal.confirm({
                    title: 'Close Job',
                    content: 'Are you sure you want to close this job?',
                    okText: 'Yes, Close',
                    cancelText: 'Cancel',
                    okType: 'danger',
                    onOk: () => {
                      closeJobMutation.mutate({
                        is_active: false,
                      });
                    },
                  });
                }}
              >
                Close Job
              </Button>
            </Space>
          )}
        </div>

        {/* INFO */}
        <Text><strong>Location:</strong> {job.location}</Text><br />
        <Text><strong>Salary:</strong> {job.salary_range || 'Not specified'}</Text><br />

        {/* SKILLS */}
        <div style={{ marginTop: 12 }}>
          <Text strong>Required Skills:</Text>
          <br />
          <Space wrap style={{ marginTop: 6 }}>
            {job.skill_requirements && job.skill_requirements.length > 0 ? (
              job.skill_requirements.map((item) => (
                <Tag key={item.id} color="blue">
                  {item.skill?.name}
                </Tag>
              ))
            ) : (
              <Text type="secondary">Not specified</Text>
            )}
          </Space>
        </div>

        {/* DEADLINE */}
        <div style={{ marginTop: 12 }}>
          <Text strong>Application Deadline: </Text>
          <Text>
            {job.deadline
              ? new Date(job.deadline).toLocaleDateString()
              : 'Not specified'}
          </Text>
        </div>

        <br />

        {/* DESCRIPTION */}
        <Title level={4}>Description</Title>
        <Text>{job.description}</Text><br /><br />

        {/* REQUIREMENTS */}
        <Title level={4}>Requirements</Title>
        <Text>{job.requirements}</Text><br /><br />

        {/* RESPONSIBILITIES */}
        <Title level={4}>Responsibilities</Title>
        <Text>{job.responsibilities}</Text>

      </Card>
    </div>
  );
};

export default JobDetail;