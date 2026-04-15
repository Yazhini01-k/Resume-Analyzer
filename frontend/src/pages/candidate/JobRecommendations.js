import React, { useState, useMemo } from 'react';

import { 

  Card, Typography, List, Tag, Button, Space, Input, Select, 

  Row, Col, Progress, Empty, Spin, message, Modal, Form 

} from 'antd';

import { 

  SearchOutlined, 

  EnvironmentOutlined, 

  DollarOutlined,

  CalendarOutlined,

  TeamOutlined

} from '@ant-design/icons';

import { useQuery, useMutation, useQueryClient } from 'react-query';

import { jobsAPI, applicationsAPI, resumeAPI } from '../../services/api';

import { useNavigate } from 'react-router-dom';



const { Title, Text, Paragraph } = Typography;

const { Option } = Select;

const { Search } = Input;



const JobRecommendations = () => {

  const [filters, setFilters] = useState({

    search: '',

    location: '',

    job_type: '',

    experience_level: '',

  });

  const [selectedJob, setSelectedJob] = useState(null);

  const [applyModalVisible, setApplyModalVisible] = useState(false);

  const [applyForm] = Form.useForm();

  const navigate = useNavigate();

  const queryClient = useQueryClient();



  // Fetch job recommendations

  const { data: recommendations, isLoading, refetch } = useQuery(

    ['job-recommendations', filters],

    () => jobsAPI.getRecommendations(),

    {

      select: (response) => {

        const data = response?.data;

        if (Array.isArray(data?.results)) {

          return data.results;

        }

        if (Array.isArray(data?.recommendations)) {

          return data.recommendations;

        }

        if (Array.isArray(data)) {

          return data;

        }

        return [];

      },

      onSuccess: (data) => {

        console.log('Recommendations loaded:', data);

      },

    }

  );



  // Fetch all jobs for search and filter options

  const { data: allJobs } = useQuery(

    'all-jobs',

    () => jobsAPI.getList({}), // Get all jobs without filters for options

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

      enabled: true, // Always fetch to get dynamic options

    }

  );



  // Extract unique locations from jobs

  const uniqueLocations = useMemo(() => {

    if (!allJobs) return [];

    const locations = [...new Set(allJobs.map(job => job.location).filter(Boolean))];

    return locations.sort();

  }, [allJobs]);



  // Extract unique job types from jobs

  const uniqueJobTypes = useMemo(() => {

    if (!allJobs) return [];

    const jobTypes = [...new Set(allJobs.map(job => job.job_type).filter(Boolean))];

    return jobTypes.sort();

  }, [allJobs]);



  // Fetch user's latest resume for application data

  const { data: userResumes } = useQuery(

    'resumes',

    resumeAPI.getList,

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

      enabled: true,

    }

  );



  // Apply mutation

  const applyMutation = useMutation(applicationsAPI.create, {

    onSuccess: (response) => {

      console.log('Application submitted successfully:', response);

      message.success('Application submitted successfully!');

      setApplyModalVisible(false);

      applyForm.resetFields();

      queryClient.invalidateQueries('applications');

      queryClient.invalidateQueries('job-recommendations');

      queryClient.invalidateQueries('resumes');

    },

    onError: (error) => {

      console.error('Application submission error:', error);

      console.error('Error response:', error.response);

      console.error('Error data:', error.response?.data);

      

      const errorMessage = error.response?.data?.error || 

                          error.response?.data?.detail || 

                          error.response?.data?.message ||

                          error.message || 

                          'Application failed. Please try again.';

      

      message.error(errorMessage);

    },

    onMutate: (variables) => {

      console.log('Starting application submission with data:', variables);

    },

  });



  const handleFilterChange = (key, value) => {

    setFilters(prev => ({ ...prev, [key]: value }));

  };



  const handleSearch = (value) => {

    setFilters(prev => ({ ...prev, search: value }));

  };



  const handleApply = (jobMatch) => {

    const job = jobMatch.job || jobMatch;

    setSelectedJob(job);

    setApplyModalVisible(true);

  };



  const handleApplySubmit = async (values) => {

    if (!userResumes?.length) {

      message.error('Please upload a resume first!');

      navigate('/candidate/resume-upload');

      return;

    }



    const latestResume = userResumes[0];

    

    console.log('=== Application Submission Debug ===');

    console.log('Selected Job:', selectedJob);

    console.log('Latest Resume:', latestResume);

    console.log('Form Values:', values);

    

    const applicationData = {

      job: selectedJob.id,

      resume: latestResume.id,

      cover_letter: values.cover_letter,

      additional_notes: values.additional_notes || '',

      // Include detailed resume data

      education_details: latestResume.extracted_education || [],

      skills_details: latestResume.extracted_skills || [],

      experience_details: latestResume.extracted_experience || [],

      // Additional fields for HR review

      cgpa: values.cgpa || '',

      arrears_history: values.arrears_history || '',

      internships: values.internships || '',

      technical_skills: values.technical_skills || latestResume.extracted_skills?.join(', ') || '',

    };



    console.log('Application Data to Send:', applicationData);

    console.log('Sending application...');

    

    applyMutation.mutate(applicationData);

  };



  const getMatchScoreColor = (score) => {

    if (score >= 80) return '#52c41a';

    if (score >= 60) return '#faad14';

    return '#f5222d';

  };



  const getJobTypeColor = (type) => {

    const colors = {

      full_time: 'blue',

      part_time: 'green',

      contract: 'orange',

      internship: 'purple',

      remote: 'cyan',

    };

    return colors[type] || 'default';

  };



  const displayJobs = filters.search || filters.location || filters.job_type || filters.experience_level 

    ? allJobs || [] 

    : recommendations || [];



  return (

    <div>

      <div className="page-header">

        <Title level={2}>Job Recommendations</Title>

        <Text type="secondary">

          Personalized job recommendations based on your resume analysis

        </Text>

      </div>



      <div className="content-wrapper">

        {/* Filters */}

        <Card style={{ marginBottom: 24 }}>

          <Row gutter={[16, 16]}>

            <Col xs={24} sm={12} md={8}>

              <Search

                placeholder="Search jobs, companies..."

                onSearch={handleSearch}

                enterButton

                allowClear

              />

            </Col>

            <Col xs={24} sm={12} md={4}>

              <Select

                placeholder="Location"

                style={{ width: '100%' }}

                allowClear

                onChange={(value) => handleFilterChange('location', value)}

                loading={!allJobs}

              >

                {uniqueLocations.map(location => (

                  <Option key={location} value={location}>

                    {location}

                  </Option>

                ))}

              </Select>

            </Col>

            <Col xs={24} sm={12} md={4}>

              <Select

                placeholder="Job Type"

                style={{ width: '100%' }}

                allowClear

                onChange={(value) => handleFilterChange('job_type', value)}

                loading={!allJobs}

              >

                {uniqueJobTypes.map(jobType => (

                  <Option key={jobType} value={jobType}>

                    {jobType?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || jobType}

                  </Option>

                ))}

              </Select>

            </Col>

            <Col xs={24} sm={12} md={4}>

              <Select

                placeholder="Experience Level"

                style={{ width: '100%' }}

                allowClear

                onChange={(value) => handleFilterChange('experience_level', value)}

              >

                <Option value="entry">Entry Level</Option>

                <Option value="mid">Mid Level</Option>

                <Option value="senior">Senior Level</Option>

                <Option value="lead">Lead Level</Option>

              </Select>

            </Col>

            <Col xs={24} sm={12} md={4}>

              <Button onClick={() => refetch()} icon={<SearchOutlined />}>

                Refresh

              </Button>

            </Col>

          </Row>

        </Card>



        {/* Job List */}

        {isLoading ? (

          <div className="loading-container">

            <Spin size="large" />

          </div>

        ) : displayJobs.length === 0 ? (

          <Empty

            description="No jobs found"

            image={Empty.PRESENTED_IMAGE_SIMPLE}

          />

        ) : (

          <List

            dataSource={displayJobs}

            renderItem={(jobMatch) => {

              console.log('JobMatch data:', jobMatch);
              console.log('JobMatch.job:', jobMatch.job);
              console.log('JobMatch.id:', jobMatch.id);

              // JobMatch object has all score breakdown fields from API

              const job = {
                id: jobMatch.job_id || jobMatch.id, // Handle both job and id fields
                title: jobMatch.job_title || jobMatch.title,
                company: jobMatch.job_company || jobMatch.company,
                description: jobMatch.description || 'Job description...',
                location: jobMatch.location || 'Location',
                job_type: jobMatch.job_type || 'full_time',
                experience_level: jobMatch.experience_level || 'mid_level',
                required_skills: jobMatch.required_skills || [],
                salary_range: jobMatch.salary_range || 'Salary range',
                created_at: jobMatch.created_at,
                application_count: jobMatch.application_count || 0,
                skill_requirements: jobMatch.skill_requirements || [],
                
                // Use dynamic scores from API response
                overall_score: jobMatch.match_percentage || jobMatch.overall_score || 0,
                skills_match_score: jobMatch.skills_match_score || 0,
                experience_match_score: jobMatch.experience_match_score || 0,
                education_match_score: jobMatch.education_match_score || 0,
                missing_skills: jobMatch.missing_skills || [],
                matched_skills: jobMatch.matched_skills || []
              };
              console.log("JOB MATCH FULL:", jobMatch);
              console.log("JOB ID:", job.id);
              const storedSkills = JSON.parse(
                localStorage.getItem(`job_skills_${job.id}`) || '[]'
              );
              console.log("STORED SKILLS:", storedSkills);

              console.log('Created job object:', job);

              return (

                <List.Item>

                  <Card 

                    className="job-card"

                    hoverable

                    actions={[

                      <Button 

                        type="primary" 

                        onClick={() => handleApply(job)}

                        loading={applyMutation.isLoading}

                      >

                        Apply Now

                      </Button>

                    ]}

                  >

                    <Row gutter={[16, 16]}>

                      <Col xs={24} md={16}>

                        <div>

                          <Title level={4} style={{ marginBottom: 8 }}>

                            {job.title}

                          </Title>

                          <Space wrap style={{ marginBottom: 12 }}>

                            <Tag color="blue">{job.company}</Tag>

                            <Tag icon={<EnvironmentOutlined />}>{job.location}</Tag>

                            <Tag color={getJobTypeColor(job.job_type)}>

                              {job.job_type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || job.job_type}

                            </Tag>

                            <Tag>{job.experience_level?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || job.experience_level}</Tag>

                          </Space>

                          

                          <Paragraph ellipsis={{ rows: 3, expandable: true }}>

                            {job.description}

                          </Paragraph>



                          
                          {job.matched_skills?.length > 0 && (
                            <div style={{ marginTop: 12 }}>
                              <Text strong>Required Skills: </Text>
                              <div style={{ marginTop: 4 }}>
                                {job.matched_skills.slice(0, 6).map((skill, index) => (
                                  <Tag key={index} size="small" color="green">
                                    {skill}
                                  </Tag>
                                ))}

                                {job.matched_skills.length > 6 && (
                                  <Tag size="small">
                                    +{job.matched_skills.length - 6} more
                                  </Tag>
                                )}
                              </div>
                            </div>
                          )}



                          <Space style={{ marginTop: 12 }}>

                            {job.salary_range && (

                              <Space>

                                <DollarOutlined />

                                <Text>{job.salary_range}</Text>

                              </Space>

                            )}

                            <Space>

                              <CalendarOutlined />

                              <Text>Posted {new Date(job.created_at).toLocaleDateString()}</Text>

                            </Space>

                            <Space>

                              <TeamOutlined />

                              <Text>{job.application_count || 0} applicants</Text>

                            </Space>

                          </Space>

                        </div>

                      </Col>

                      

                      <Col xs={24} md={8}>

                        <div style={{ textAlign: 'center', padding: '20px' }}>

                          <div className="match-score" style={{ 

                            color: getMatchScoreColor(jobMatch.overall_score || 0),

                            fontSize: '24px',

                            fontWeight: 'bold'

                          }}>

                            {(jobMatch.overall_score || 0).toFixed(1)}%

                          </div>

                          <Text type="secondary">Match Score</Text>

                          <Progress 

                            percent={jobMatch.overall_score || 0} 

                            strokeColor={getMatchScoreColor(jobMatch.overall_score || 0)}

                            showInfo={false}

                            style={{ marginTop: 8 }}

                          />

                          

                          <div style={{ marginTop: 16, textAlign: 'left' }}>

                            <div style={{ marginBottom: 4 }}>

                              <Text strong>Skills Match: </Text>

                              <Text>{(jobMatch.skills_match_score || 0).toFixed(1)}%</Text>

                            </div>

                            <div style={{ marginBottom: 4 }}>

                              <Text strong>Experience: </Text>

                              <Text>{(jobMatch.experience_match_score || 0).toFixed(1)}%</Text>

                            </div>

                            <div>
                              {/*

                              <Text strong>Education: </Text>

                              <Text>{(jobMatch.education_match_score || 0).toFixed(1)}%</Text>
                              */}

                            </div>

                          </div>



                          {jobMatch.missing_skills && jobMatch.missing_skills.length > 0 && (

                            <div style={{ marginTop: 12 }}>

                              <Text strong type="secondary">Missing Skills:</Text>

                              <div style={{ marginTop: 4 }}>

                                {jobMatch.missing_skills.slice(0, 3).map((skill, index) => (

                                  <Tag key={index} size="small" color="orange">{skill}</Tag>

                                ))}

                                {jobMatch.missing_skills.length > 3 && (

                                  <Tag size="small" color="orange">+{jobMatch.missing_skills.length - 3} more</Tag>

                                )}

                              </div>

                            </div>

                          )}

                        </div>

                      </Col>

                    </Row>

                  </Card>

                </List.Item>

              );

            }}

          />

        )}



        {/* Apply Modal */}

        <Modal

          title={`Apply for ${selectedJob?.title}`}

          open={applyModalVisible}

          onCancel={() => setApplyModalVisible(false)}

          footer={null}

          width={600}

        >

          <Form

            form={applyForm}

            layout="vertical"

            onFinish={handleApplySubmit}

          >

            <Form.Item

              name="cover_letter"

              label="Cover Letter"

              rules={[{ required: true, message: 'Please write a cover letter!' }]}

            >

              <Input.TextArea

                rows={6}

                placeholder="Tell us why you're interested in this position and why you'd be a great fit..."

              />

            </Form.Item>



            {/* Education Details */}

            <Form.Item

              name="cgpa"

              label="CGPA (Grade Point Average)"

              rules={[{ required: true, message: 'Please enter your CGPA!' }]}

            >

              <Input 

                placeholder="e.g., 8.5/10 or 3.8/4.0"

                addonAfter="/10"

              />

            </Form.Item>



            <Form.Item

              name="arrears_history"

              label="Arrears History (if any)"

            >

              <Input.TextArea

                rows={2}

                placeholder="Please mention any arrears/backlogs if applicable (write 'None' if no arrears)"

              />

            </Form.Item>



            <Form.Item

              name="internships"

              label="Internship Experience"

            >

              <Input.TextArea

                rows={3}

                placeholder="List your internship experiences with company name, duration, and role..."

              />

            </Form.Item>



            <Form.Item

              name="technical_skills"

              label="Technical Skills"

              rules={[{ required: true, message: 'Please list your technical skills!' }]}

            >

              <Input.TextArea

                rows={2}

                placeholder="e.g., Python, Java, React, SQL, Machine Learning, etc."

              />

            </Form.Item>



            <Form.Item

              name="additional_notes"

              label="Additional Notes (Optional)"

            >

              <Input.TextArea

                rows={3}

                placeholder="Any additional information you'd like to share..."

              />

            </Form.Item>



            <Form.Item>

              <Space>

                <Button 

                  type="primary" 

                  htmlType="submit"

                  loading={applyMutation.isLoading}

                >

                  Submit Application

                </Button>

                <Button onClick={() => setApplyModalVisible(false)}>

                  Cancel

                </Button>

              </Space>

            </Form.Item>

          </Form>

        </Modal>

      </div>

    </div>

  );

};



// Add custom styles

const styles = `

  .job-card {

    margin-bottom: 16px;

    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    border-radius: 8px;

  }

  

  .job-card:hover {

    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);

    transform: translateY(-2px);

    transition: all 0.3s ease;

  }

  

  .match-score {

    font-size: 28px;

    font-weight: bold;

    margin-bottom: 8px;

  }

  

  .loading-container {

    display: flex;

    justify-content: center;

    align-items: center;

    height: 200px;

  }

  

  .ant-list-item {

    padding: 0 0 16px 0 !important;

  }

`;



// Inject styles

if (typeof document !== 'undefined') {

  const styleSheet = document.createElement('style');

  styleSheet.textContent = styles;

  document.head.appendChild(styleSheet);

}



export default JobRecommendations;