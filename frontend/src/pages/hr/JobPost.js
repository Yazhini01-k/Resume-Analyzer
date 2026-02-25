import React, { useState } from 'react';
import { Card, Typography, Form, Input, Select, Button, message, Space, Row, Col } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { jobsAPI } from '../../services/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const JobPost = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();

  // Fetch job skills for selection
  const { data: jobSkills } = useQuery(
    'job-skills',
    jobsAPI.getSkills,
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

  // Create job mutation
  const createJobMutation = useMutation(jobsAPI.create, {
    onSuccess: () => {
      message.success('Job posted successfully!');
      form.resetFields();
      queryClient.invalidateQueries('my-posted-jobs');
      setLoading(false);
    },
    onError: (error) => {
      message.error(error.response?.data?.title?.[0] || 'Failed to post job. Please try again.');
      setLoading(false);
    },
  });

  const handleSubmit = async (values) => {
    setLoading(true);
    
    // Format the data for API
    const jobData = {
      ...values,
      skill_requirements: Array.isArray(values.required_skills) 
        ? values.required_skills.map((skillId, index) => ({
            skill_id: skillId,
            importance: 'required',
            experience_years: 0,
          }))
        : [],
    };

    try {
      await createJobMutation.mutateAsync(jobData);
    } catch (error) {
      console.error('Job posting error:', error);
    }
  };

  return (
    <div>
      <div className="page-header">
        <Title level={2}>Post New Job</Title>
        <Text type="secondary">
          Create a new job posting to attract qualified candidates
        </Text>
      </div>

      <div className="content-wrapper">
        <Card>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{
              job_type: 'full_time',
              experience_level: 'mid',
            }}
          >
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="title"
                  label="Job Title"
                  rules={[{ required: true, message: 'Please enter job title!' }]}
                >
                  <Input placeholder="e.g., Senior Software Engineer" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  name="company"
                  label="Company Name"
                  rules={[{ required: true, message: 'Please enter company name!' }]}
                >
                  <Input placeholder="e.g., Tech Corp" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="location"
                  label="Location"
                  rules={[{ required: true, message: 'Please enter location!' }]}
                >
                  <Input placeholder="e.g., San Francisco, CA or Remote" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  name="salary_range"
                  label="Salary Range"
                >
                  <Input placeholder="e.g., $80,000 - $120,000" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="job_type"
                  label="Job Type"
                  rules={[{ required: true, message: 'Please select job type!' }]}
                >
                  <Select placeholder="Select job type">
                    <Option value="full_time">Full Time</Option>
                    <Option value="part_time">Part Time</Option>
                    <Option value="contract">Contract</Option>
                    <Option value="internship">Internship</Option>
                    <Option value="remote">Remote</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  name="experience_level"
                  label="Experience Level"
                  rules={[{ required: true, message: 'Please select experience level!' }]}
                >
                  <Select placeholder="Select experience level">
                    <Option value="entry">Entry Level</Option>
                    <Option value="mid">Mid Level</Option>
                    <Option value="senior">Senior Level</Option>
                    <Option value="lead">Lead Level</Option>
                    <Option value="executive">Executive</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="description"
              label="Job Description"
              rules={[{ required: true, message: 'Please enter job description!' }]}
            >
              <TextArea
                rows={6}
                placeholder="Provide a detailed description of the role, responsibilities, and what you're looking for in a candidate..."
              />
            </Form.Item>

            <Form.Item
              name="requirements"
              label="Requirements"
              rules={[{ required: true, message: 'Please enter job requirements!' }]}
            >
              <TextArea
                rows={4}
                placeholder="List the specific requirements, qualifications, and skills needed for this position..."
              />
            </Form.Item>

            <Form.Item
              name="responsibilities"
              label="Responsibilities"
            >
              <TextArea
                rows={4}
                placeholder="Describe the day-to-day responsibilities and duties of this role..."
              />
            </Form.Item>

            <Form.Item
              name="required_skills"
              label="Required Skills"
              rules={[{ required: true, message: 'Please select at least one required skill!' }]}
            >
              <Select
                mode="multiple"
                placeholder="Select required skills"
                style={{ width: '100%' }}
              >
                {Array.isArray(jobSkills) && jobSkills.map((skill) => (
                  <Option key={skill.id} value={skill.id}>
                    {skill.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="deadline"
              label="Application Deadline"
            >
              <Input type="date" />
            </Form.Item>

            <Form.Item
              name="external_url"
              label="External Job URL"
            >
              <Input placeholder="Link to job posting on external site (optional)" />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<SaveOutlined />}
                >
                  Post Job
                </Button>
                <Button onClick={() => form.resetFields()}>
                  Reset
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>

        {/* Tips Section */}
        <Card title="Tips for Effective Job Postings" style={{ marginTop: 24 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Card size="small">
                <Title level={5}>Be Specific</Title>
                <Text type="secondary">
                  Provide clear details about responsibilities, requirements, and expectations to attract the right candidates.
                </Text>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card size="small">
                <Title level={5}>Highlight Benefits</Title>
                <Text type="secondary">
                  Mention company culture, growth opportunities, and unique benefits to stand out from other postings.
                </Text>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card size="small">
                <Title level={5}>Use Relevant Keywords</Title>
                <Text type="secondary">
                  Include industry-specific terms and skills that qualified candidates will search for.
                </Text>
              </Card>
            </Col>
          </Row>
        </Card>
      </div>
    </div>
  );
};

export default JobPost;
