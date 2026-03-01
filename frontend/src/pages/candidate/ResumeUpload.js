import React, { useState } from 'react';
import { Card, Typography, Upload, message, Progress, Tag, Space, Row, Col, Statistic, Button, Modal, Spin, Popconfirm } from 'antd';
import { InboxOutlined, FileTextOutlined, CheckCircleOutlined, ClockCircleOutlined, BarChartOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { resumeAPI } from '../../services/api';



const { Title, Text, Paragraph } = Typography;

const { Dragger } = Upload;



const ResumeUpload = () => {

  const [uploading, setUploading] = useState(false);

  const [uploadProgress, setUploadProgress] = useState(0);

  const [analysisModalVisible, setAnalysisModalVisible] = useState(false);

  const [selectedResume, setSelectedResume] = useState(null);

  const [showTopAnalysis, setShowTopAnalysis] = useState(
  sessionStorage.getItem("showTopAnalysis") === "true"
);

  const queryClient = useQueryClient();

  // Fetch existing resumes with real-time updates

  const { data: resumes } = useQuery(

    'resumes',

    resumeAPI.getList,

    {

      select: (response) =>
        Array.isArray(response?.data?.results)
          ? response.data.results
          : response?.data || [],

      refetchInterval: (data) => {

        // Refetch every 2 seconds if there are processing resumes

        const resumeData = data?.data || [];

        const hasProcessing = Array.isArray(resumeData) && resumeData.some(resume => resume.processing_status === 'processing');

        return hasProcessing ? 2000 : false;

      },

    }

  );



  // Upload mutation

  const uploadMutation = useMutation(resumeAPI.upload, {

    onSuccess: (data) => {

      console.log('Upload successful:', data);

      message.success('Resume uploaded successfully! Processing will begin shortly.');

      setUploading(false);

      setUploadProgress(100);

      setShowTopAnalysis(true);
      sessionStorage.setItem("showTopAnalysis", "true");
      

      // Invalidate queries to refresh data

      queryClient.invalidateQueries('resumes');

      

      // // After 2 seconds, redirect to job recommendations

      // setTimeout(() => {

      //   message.info('Redirecting to job recommendations...');

      //   window.location.href = '/candidate/job-recommendations';

      // }, 2000);

    },

    onError: (error) => {

      console.error('Upload error:', error);

      const errorMessage = error.response?.data?.file?.[0] || 

                          error.response?.data?.message || 

                          error.message || 

                          'Upload failed. Please try again.';

      message.error(errorMessage);

      setUploading(false);

      setUploadProgress(0);

    },

  });



  // Delete mutation
  const deleteMutation = useMutation(resumeAPI.delete, {
    onSuccess: () => {
      message.success('Resume deleted successfully!');
      queryClient.invalidateQueries('resumes');
    },
    onError: (error) => {
      console.error('Delete error:', error);
      const errorMessage = error.response?.data?.message || 
                          error.message || 
                          'Failed to delete resume. Please try again.';
      message.error(errorMessage);
    },
  });

  // Reprocess mutation
  const reprocessMutation = useMutation(resumeAPI.reprocess, {
    onSuccess: () => {
      message.success('Resume reprocessing started!');
      queryClient.invalidateQueries('resumes');
    },
    onError: (error) => {
      console.error('Reprocess error:', error);
      const errorMessage = error.response?.data?.message || 
                          error.message || 
                          'Failed to reprocess resume. Please try again.';
      message.error(errorMessage);
    },
  });



  const uploadProps = {

    name: 'file',

    multiple: false,

    accept: '.pdf,.docx,.jpg,.jpeg,.png',

    beforeUpload: (file) => {

      console.log('beforeUpload called with file:', file.name, file.type);

      

      // Check file size (5MB limit)

      const isLt5M = file.size / 1024 / 1024 < 5;

      if (!isLt5M) {

        message.error('File must be smaller than 5MB!');

        return false;

      }



      // Check file type

      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 

                          'image/jpeg', 'image/jpg', 'image/png'];

      if (!allowedTypes.includes(file.type)) {

        message.error('Only PDF, DOCX, and image files are allowed!');

        return false;

      }



      console.log('File validation passed, calling handleUpload...');

      // Trigger the upload

      handleUpload(file);

      return false; // Prevent default upload behavior

    },

    onChange: (info) => {

      const { file } = info;

      if (file.status === 'uploading') {

        setUploadProgress(Math.round(file.percent || 0));

      }

    },

  };



  const handleUpload = async (file) => {

    console.log('Upload started for file:', file.name, 'Type:', file.type, 'Size:', file.size);

    

    const formData = new FormData();

    formData.append('file', file);

    formData.append('title', file.name.replace(/\.[^/.]+$/, '')); // Remove extension



    console.log('FormData entries:');

    for (let [key, value] of formData.entries()) {

      console.log(`${key}:`, value);

    }



    setUploading(true);

    setUploadProgress(0);



    // Simulate progress

    const progressInterval = setInterval(() => {

      setUploadProgress(prev => {

        if (prev >= 90) {

          clearInterval(progressInterval);

          return 90;

        }

        return prev + 10;

      });

    }, 200);



    try {

      console.log('Calling uploadMutation...');

      const result = await uploadMutation.mutateAsync(formData);

      console.log('Upload successful! Result:', result);

      setUploadProgress(100);

    } catch (error) {

      console.error('Upload error:', error);

      clearInterval(progressInterval);

    }

  };



  const handleDrop = (e) => {

    const files = e.dataTransfer.files;

    if (files.length > 0) {

      handleUpload(files[0]);

    }

  };



  return (

    <div>

      <div className="page-header">

        <Title level={2}>Resume Upload</Title>

        <Text type="secondary">

          Upload your resume to get AI-powered analysis and job recommendations

        </Text>

      </div>



      <div className="content-wrapper">

        <Row gutter={[16, 16]}>

          {/* Upload Section */}

          <Col xs={24} lg={12}>

            <Card title="Upload Resume">

              <div

                className="upload-area"

                onDrop={handleDrop}

                onDragOver={(e) => e.preventDefault()}

              >

                <Dragger {...uploadProps} disabled={uploading}>

                  <p className="ant-upload-drag-icon">

                    <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />

                  </p>

                  <p className="ant-upload-text">

                    Click or drag file to this area to upload

                  </p>

                  <p className="ant-upload-hint">

                    Support for PDF, DOCX, and image files. Maximum file size: 5MB.

                  </p>

                </Dragger>

              </div>



              {uploading && (

                <div style={{ marginTop: 16 }}>

                  <Text>Uploading and processing...</Text>

                  <Progress percent={uploadProgress} status="active" />

                </div>

              )}



              {/* Latest Resume Analysis - Unified Layout */}

              {showTopAnalysis && Array.isArray(resumes) && resumes.length > 0 && (

                <div style={{ marginTop: 24 }}>

                  {(() => {

                    const latestResume = resumes[0];

                    if (!latestResume) return null;

                    return (

                      <Card className="unified-resume-card" style={{ maxWidth: 400, margin: '0 auto' }}>

                        <Row gutter={[16, 16]}>

                          {/* Left Section - Resume Score */}

                          <Col xs={24} md={8} lg={12}>

                            <div style={{ textAlign: 'center', padding: '0 4px 8px 4px' }}>

                              <Title level={3} style={{ margin:'4px 0', color: '#1890ff', fontSize: '34px', fontStyle: 'times new roman' }}>

                                Resume Score

                              </Title>

                              {latestResume.analysis ? (

                                <>

                                  <div style={{

                                    fontSize: '60px',

                                    fontWeight: 'bold',

                                    color: latestResume.analysis.overall_score >= 80 ? '#52c41a' : 

                                           latestResume.analysis.overall_score >= 60 ? '#fa8c16' : '#ff4d4f',

                                    margin: '8px 0',

                                    lineHeight: 1.5

                                  }}>

                                    {latestResume.analysis.overall_score.toFixed(1)}%

                                  </div>

                                  <Progress 

                                    percent={latestResume.analysis.overall_score} 

                                    strokeColor={latestResume.analysis.overall_score >= 80 ? '#52c41a' : 

                                               latestResume.analysis.overall_score >= 60 ? '#fa8c16' : '#ff4d4f'}

                                    strokeWidth={16}

                                    style={{ marginBottom: 20 }}

                                  />

                                  <div style={{ fontSize: '16px', color: '#666', fontWeight: '500' }}>

                                    {latestResume.analysis.overall_score >= 80 ? 'Excellent Resume' :

                                     latestResume.analysis.overall_score >= 60 ? 'Good Resume' : 'Needs Improvement'}

                                  </div>

                                </>

                              ) : (

                                <div style={{ textAlign: 'center', padding: '40px' }}>

                                  <Spin size="large" />

                                  <div style={{ marginTop: 16 }}>

                                    <Text style={{ fontSize: '16px' }}>Analyzing resume...</Text>

                                  </div>

                                </div>

                              )}

                            </div>

                          </Col>



                          {/* Middle Section - Skills */}

                          <Col xs={24} md={8}>

                            <div style={{ padding: '0px 12px 12px 12px' }}>

                              <Title level={4} style={{ margin: 8, color: '#52c41a' }}>

                                Skills

                              </Title>

                              {Array.isArray(latestResume.extracted_skills) && latestResume.extracted_skills.length > 0 ? (

                                <div>

                                  <div style={{ marginBottom: 16 }}>

                                    <Text strong style={{ color: '#52c41a', fontSize: '16px' }}>

                                      {latestResume.extracted_skills.length} Skills Found

                                    </Text>

                                  </div>

                                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>

                                    <Space direction="vertical" size="small" style={{ width: '100%' }}>

                                     {Array.from(
                                        new Set(
                                          latestResume.extracted_skills.map(skill =>
                                            skill.trim().toLowerCase()
                                          )
                                        )
                                      ).map((skill, index) => (
                                        <div key={index} style={{ 
                                          display: 'flex', 
                                          justifyContent: 'space-between', 
                                          alignItems: 'center',
                                          padding: '12px 16px',
                                          backgroundColor: '#f6ffed',
                                          borderRadius: '8px',
                                          border: '1px solid #b7eb8f'
                                        }}>
                                          <Text style={{ fontSize: '14px', fontWeight: '500' }}>
                                            {skill.charAt(0).toUpperCase() + skill.slice(1)}
                                          </Text>
                                          <Tag color="green" size="small" style={{ fontWeight: 'bold' }}>85%</Tag>
                                        </div>
                                      ))}

                                    </Space>

                                  </div>

                                </div>

                              ) : (

                                <div style={{ textAlign: 'center', padding: '40px' }}>

                                  <Text type="secondary" style={{ fontSize: '16px' }}>No skills extracted yet</Text>

                                </div>

                              )}

                            </div>

                          </Col>



                          {/* Right Section - Education & Experience */}

                          <Col xs={24} md={8}>

                            <div style={{ padding: '0px 12px 12px 12px' }}>

                              {/* Education */}

                              <div style={{ marginBottom: 20 }}>

<<<<<<< HEAD
                                <Title level={4} style={{ marginBottom: 8, color: '#fa8c16' }}>
=======
                                <Title level={4} style={{ marginBottom: 8 , color: '#fa8c16' }}>
>>>>>>> 361e808 (did small changes in UI, fixes repeated skill and now checking if homepage works)

                                  Education

                                </Title>

                                {Array.isArray(latestResume.extracted_education) && latestResume.extracted_education.length > 0 ? (

                                  <div>

                                    {latestResume.extracted_education.map((edu, index) => (

                                      <div key={index} style={{ 

                                        marginBottom: '16px',

                                        padding: '16px',

                                        backgroundColor: '#fff7e6',

                                        borderRadius: '8px',

                                        border: '1px solid #ffd591'

                                      }}>

                                        <Text strong style={{ color: '#fa8c16', fontSize: '16px' }}>

                                          {edu.degree || 'Bachelor Degree'}

                                        </Text>

                                        <br />

                                        <Text style={{ fontSize: '14px', color: '#666', marginTop: '4px', display: 'block' }}>

                                          {edu.institution || 'University'}

                                        </Text>

                                        <Text type="secondary" style={{ fontSize: '12px', marginTop: '4px', display: 'block' }}>

                                          {edu.year || '2020'} • {edu.field || 'Computer Science'}

                                        </Text>

                                      </div>

                                    ))}

                                  </div>

                                ) : (

                                  <div style={{ 

                                    textAlign: 'center', 

                                    padding: '20px',

                                    backgroundColor: '#fff7e6',

                                    borderRadius: '8px',

                                    border: '1px solid #ffd591'

                                  }}>

                                    <Text type="secondary">No education details found</Text>

                                  </div>

                                )}

                              </div>



                              {/* Experience */}

                              <div>

                                <Title level={4} style={{ marginBottom: 16, color: '#722ed1' }}>

                                  Experience

                                </Title>

                                {Array.isArray(latestResume.extracted_experience) && latestResume.extracted_experience.length > 0 ? (

                                  <div>

                                    {latestResume.extracted_experience.map((exp, index) => (

                                      <div key={index} style={{ 

                                        marginBottom: '16px',

                                        padding: '16px',

                                        backgroundColor: '#f9f0ff',

                                        borderRadius: '8px',

                                        border: '1px solid #d3adf7'

                                      }}>

                                        <Text strong style={{ color: '#722ed1', fontSize: '16px' }}>

                                          {exp.position || exp.title || 'Software Engineer'}

                                        </Text>

                                        <br />

                                        <Text style={{ fontSize: '14px', color: '#666', marginTop: '4px', display: 'block' }}>

                                          {exp.company || 'Tech Company'}

                                        </Text>

                                        <Text type="secondary" style={{ fontSize: '12px', marginTop: '4px', display: 'block' }}>

                                          {exp.duration || exp.years ? `${exp.duration || exp.years} years` : '2 years'}

                                        </Text>

                                      </div>

                                    ))}

                                  </div>

                                ) : (

                                  <div style={{ 

                                    textAlign: 'center', 

                                    padding: '20px',

                                    backgroundColor: '#f9f0ff',

                                    borderRadius: '8px',

                                    border: '1px solid #d3adf7'

                                  }}>

                                    <Text type="secondary">No experience details found</Text>

                                  </div>

                                )}

                              </div>

                            </div>

                          </Col>

                        </Row>

                      </Card>

                    );

                  })()}

                </div>

              )}



              <div style={{ marginTop: 16 }}>

                <Title level={5}>Supported Formats:</Title>

                <Space wrap>

                  <Tag color="blue">PDF</Tag>

                  <Tag color="blue">DOCX</Tag>

                  <Tag color="blue">JPG</Tag>

                  <Tag color="blue">PNG</Tag>

                </Space>

              </div>

            </Card>

          </Col>



          {/* Instructions */}

          <Col xs={24} lg={12}>

            <Card title="How it works">

              <Space direction="vertical" size="large" style={{ width: '100%' }}>

                <div>

                  <Title level={5}>

                    <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />

                    Upload Your Resume

                  </Title>

                  <Paragraph>

                    Upload your resume in PDF, DOCX, or image format. Our system will automatically extract text content.

                  </Paragraph>

                  <div style={{ marginTop: 16 }}>

                    <Button 

                      type="link" 

                      icon={<FileTextOutlined />}

                      onClick={() => window.location.href = '/candidate/job-recommendations'}

                    >

                      View Job Recommendations

                    </Button>

                  </div>

                </div>



                <div>

                  <Title level={5}>

                    <ClockCircleOutlined style={{ color: '#1890ff', marginRight: 8 }} />

                    AI Processing

                  </Title>

                  <Paragraph>

                    Our AI analyzes your resume to extract skills, experience, education, and creates a feature vector for matching.

                  </Paragraph>

                </div>



                <div>

                  <Title level={5}>

                    <FileTextOutlined style={{ color: '#722ed1', marginRight: 8 }} />

                    Get Analysis

                  </Title>

                  <Paragraph>

                    Receive detailed analysis including skills assessment, completeness score, and improvement suggestions.

                  </Paragraph>

                </div>



                <div>

                  <Title level={5}>

                    <CheckCircleOutlined style={{ color: '#fa8c16', marginRight: 8 }} />

                    Job Recommendations

                  </Title>

                  <Paragraph>

                    Get personalized job recommendations based on your skills and experience with match percentages.

                  </Paragraph>

                </div>

              </Space>

            </Card>

          </Col>

        </Row>



        {/* Existing Resumes */}

        {Array.isArray(resumes) && resumes.length > 0 && (

          <Card title="Your Resumes" style={{ marginTop: 24 }}>

            <Row gutter={[16, 16]}>

              {resumes.map((resume) => (

                <Col xs={24} sm={12} lg={8} key={resume.id}>

                  <Card 

                    size="small"

                    hoverable

                    className="resume-card"

                    actions={[
                      ...(resume.processing_status === 'completed' ? [
                        <Button 
                          key={`analysis-${resume.id}`}
                          type="primary"
                          icon={<BarChartOutlined />}
                          onClick={() => {
                            setSelectedResume(resume);
                            setAnalysisModalVisible(true);
                          }}
                          style={{ 
                            background: 'white', 
                            color: '#667eea',
                            border: 'none',
                            fontWeight: 'bold'
                          }}
                        >
                          View Detailed Analysis
                        </Button>
                      ] : []),
                      ...(resume.processing_status === 'processing' ? [
                        <Button 
                          key={`processing-${resume.id}`}
                          type="default"
                          icon={<BarChartOutlined />}
                          onClick={() => {
                            message.info('Resume is still being processed. Please wait...');
                          }}
                          style={{ 
                            background: '#f0f0f0', 
                            color: '#666',
                            border: '1px solid #d9d9d9'
                          }}
                        >
                          Processing...
                        </Button>
                      ] : []),
                      ...(resume.processing_status === 'failed' ? [
                        <Button 
                          key={`reprocess-${resume.id}`}
                          type="default"
                          icon={<ReloadOutlined />}
                          onClick={() => reprocessMutation.mutate(resume.id)}
                          loading={reprocessMutation.isLoading}
                          style={{ 
                            background: '#fff7e6', 
                            color: '#fa8c16',
                            border: '1px solid #ffd591'
                          }}
                        >
                          Re-process Resume
                        </Button>
                      ] : []),
                      // Delete button - always available with unique key
                      <Popconfirm
                        key={`delete-${resume.id}`}
                        title="Are you sure you want to delete this resume?"
                        description="This action cannot be undone."
                        onConfirm={() => {
                          console.log('Deleting resume with ID:', resume.id);
                          deleteMutation.mutate(resume.id);
                        }}
                        okText="Yes, Delete"
                        cancelText="Cancel"
                        okButtonProps={{ danger: true }}
                      >
                        <Button 
                          type="primary"
                          danger
                          loading={deleteMutation.isLoading}
                          style={{ 
                            background: '#fff2f0', 
                            color: '#ff4d4f',
                            border: '1px solid #ffccc7',
                            fontWeight: 'bold'
                          }}
                        >
                          Delete
                        </Button>
                      </Popconfirm>
                    ]}

                    extra={
                      resume.analysis && (

                        <div style={{ textAlign: 'center' }}>

                          <div style={{

                            fontSize: '14px',

                            fontWeight: 'bold',

                            color: resume.analysis.overall_score >= 80 ? '#3f8600' : 

                                   resume.analysis.overall_score >= 60 ? '#fa8c16' : '#cf1322',

                            padding: '2px 8px',

                            borderRadius: '12px',

                            backgroundColor: resume.analysis.overall_score >= 80 ? '#f6ffed' : 

                                             resume.analysis.overall_score >= 60 ? '#fff7e6' : '#fff1f0',

                            border: `1px solid ${resume.analysis.overall_score >= 80 ? '#b7eb8f' : 

                                              resume.analysis.overall_score >= 60 ? '#ffd591' : '#ffccc7'}`

                          }}>

                            {resume.analysis.overall_score.toFixed(1)}%

                          </div>

                        </div>

                      )

                    }

                  >

                    <div style={{ textAlign: 'center' }}>

                      <FileTextOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 8 }} />

                      <Title level={5} style={{ margin: 0 }}>{resume.title}</Title>

                      <Text type="secondary" style={{ fontSize: 12 }}>

                        {resume.file_type.toUpperCase()} • {(resume.file_size / 1024 / 1024).toFixed(2)} MB

                      </Text>

                      

                      <div style={{ marginTop: 12 }}>

                        <Tag 

                          color={

                            resume.processing_status === 'completed' ? 'green' :

                            resume.processing_status === 'processing' ? 'blue' :

                            resume.processing_status === 'failed' ? 'red' : 'orange'

                          }

                        >

                          {resume.processing_status}

                        </Tag>

                      </div>



                      {resume.analysis && (

                        <div style={{ marginTop: 12, textAlign: 'center' }}>

                          <div style={{

                            fontSize: '24px',

                            fontWeight: 'bold',

                            color: resume.analysis.overall_score >= 80 ? '#3f8600' : 

                                   resume.analysis.overall_score >= 60 ? '#fa8c16' : '#cf1322',

                            marginBottom: '4px'

                          }}>

                            {resume.analysis.overall_score.toFixed(1)}%

                          </div>

                          <Text type="secondary" style={{ fontSize: '12px' }}>

                            Resume Score

                          </Text>

                          <Progress 

                            percent={resume.analysis.overall_score} 

                            strokeColor={resume.analysis.overall_score >= 80 ? '#3f8600' : 

                                       resume.analysis.overall_score >= 60 ? '#fa8c16' : '#cf1322'}

                            showInfo={false}

                            size="small"

                            style={{ marginTop: '4px' }}

                          />

                          

                          {Array.isArray(resume.extracted_skills) && resume.extracted_skills.length > 0 && (

                            <div style={{ marginTop: 8 }}>

                              <Tag color="blue" size="small">

                                {resume.extracted_skills.length} Skills Found

                              </Tag>

                              <div style={{ marginTop: 4 }}>

                                <Space wrap size="small">

                                  {resume.extracted_skills.slice(0, 3).map((skill, index) => (

                                    <Tag key={index} size="small" color="geekblue">{skill}</Tag>

                                  ))}

                                  {resume.extracted_skills.length > 3 && (

                                    <Tag size="small" color="default">+{resume.extracted_skills.length - 3}</Tag>

                                  )}

                                </Space>

                              </div>

                            </div>

                          )}

                        </div>

                      )}



                      <div style={{ marginTop: 12 }}>

                        <Text type="secondary" style={{ fontSize: 11 }}>

                          Uploaded: {new Date(resume.created_at).toLocaleDateString()}

                        </Text>

                      </div>

                    </div>

                  </Card>

                </Col>

              ))}

            </Row>

          </Card>

        )}

      </div>



      {/* Analysis Modal */}

      <Modal

        title={`Resume Analysis - ${selectedResume?.title}`}

        open={analysisModalVisible}

        onCancel={() => setAnalysisModalVisible(false)}

        footer={null}

        width={800}

      >

        {selectedResume && (

          <div>

            {/* Overall Score */}

            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>

              <Col xs={24} md={8}>

                <Card>

                  <Statistic

                    title="Overall Score"

                    value={selectedResume.analysis?.overall_score || 0}

                    precision={1}

                    suffix="%"

                    valueStyle={{

                      color: selectedResume.analysis?.overall_score >= 80 ? '#3f8600' : 

                             selectedResume.analysis?.overall_score >= 60 ? '#fa8c16' : '#cf1322'

                    }}

                  />

                </Card>

              </Col>

              <Col xs={24} md={8}>

                <Card>

                  <Statistic

                    title="Skills Found"

                    value={selectedResume.extracted_skills?.length || 0}

                    prefix={<BarChartOutlined />}

                  />

                </Card>

              </Col>

              <Col xs={24} md={8}>

                <Card>

                  <Statistic

                    title="Completeness"

                    value={selectedResume.analysis?.completeness_score || 0}

                    precision={1}

                    suffix="%"

                    valueStyle={{

                      color: selectedResume.analysis?.completeness_score >= 80 ? '#3f8600' : 

                             selectedResume.analysis?.completeness_score >= 60 ? '#fa8c16' : '#cf1322'

                    }}

                  />

                </Card>

              </Col>

            </Row>



            {/* Detailed Analysis */}

            <Row gutter={[16, 16]}>

              <Col xs={24} md={12}>

                <Card title="Extracted Skills" size="small">

                  <div style={{ maxHeight: 200, overflowY: 'auto' }}>

                    {Array.isArray(selectedResume.extracted_skills) && selectedResume.extracted_skills.length > 0 ? (

                      <Space wrap>

                        {selectedResume.extracted_skills.map((skill, index) => (

                          <Tag key={index} color="blue">{skill}</Tag>

                        ))}

                      </Space>

                    ) : (

                      <Text type="secondary">No skills extracted</Text>

                    )}

                  </div>

                </Card>

              </Col>

              <Col xs={24} md={12}>

                <Card title="Education Details" size="small">

                  {Array.isArray(selectedResume.extracted_education) && selectedResume.extracted_education.length > 0 ? (

                    <div>

                      {selectedResume.extracted_education.map((edu, index) => (

                        <div key={index} style={{ marginBottom: 8 }}>

                          <Text strong>{edu.degree || edu.institution}</Text>

                          <br />

                          <Text type="secondary" style={{ fontSize: 12 }}>

                            {edu.year && `${edu.year} • `} 

                            {edu.field && edu.field}

                          </Text>

                        </div>

                      ))}

                    </div>

                  ) : (

                    <Text type="secondary">No education details found</Text>

                  )}

                </Card>

              </Col>

            </Row>



            {/* Experience Details */}

            {Array.isArray(selectedResume.extracted_experience) && selectedResume.extracted_experience.length > 0 && (

              <Row gutter={[16, 16]} style={{ marginTop: 16 }}>

                <Col xs={24}>

                  <Card title="Work Experience" size="small">

                    <div style={{ maxHeight: 200, overflowY: 'auto' }}>

                      {selectedResume.extracted_experience.map((exp, index) => (

                        <div key={index} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: '1px solid #f0f0f0' }}>

                          <Text strong>{exp.position || exp.title}</Text>

                          <br />

                          <Text type="secondary" style={{ fontSize: 12 }}>

                            {exp.company && `${exp.company} • `}

                            {exp.duration && exp.duration}

                            {exp.years && `${exp.years} years`}

                          </Text>

                          {exp.description && (

                            <div style={{ marginTop: 4 }}>

                              <Text style={{ fontSize: 12 }}>{exp.description}</Text>

                            </div>

                          )}

                        </div>

                      ))}

                    </div>

                  </Card>

                </Col>

              </Row>

            )}

          </div>

        )}

      </Modal>

    </div>

  );

};



// Add custom styles

const styles = `
  .upload-area {
    border: 2px dashed #d9d9d9;
    border-radius: 8px;
    padding: 40px;
    text-align: center;
    background: #fafafa;
    transition: all 0.3s ease;

  }
  
  .upload-area:hover {
    border-color: #1890ff;
    background: #f0f8ff;
  }

  .unified-resume-card {
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    border: 1px solid #e8e8e8;
    background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
    transition: all 0.3s ease;
  }

  .unified-resume-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  }

  .resume-score-card {
    text-align: center;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(24, 144, 255, 0.15);
    border: 2px solid #e6f7ff;
    background: linear-gradient(135deg, #f0f8ff 0%, #ffffff 100%);
  }

  .skills-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(82, 196, 26, 0.15);
    border: 2px solid #f6ffed;
    background: linear-gradient(135deg, #f6ffed 0%, #ffffff 100%);
  }

  .education-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(250, 140, 22, 0.15);
    border: 2px solid #fff7e6;
    background: linear-gradient(135deg, #fff7e6 0%, #ffffff 100%);
  }

  .experience-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(114, 46, 209, 0.15);
    border: 2px solid #f9f0ff;
    background: linear-gradient(135deg, #f9f0ff 0%, #ffffff 100%);
  }

  .analysis-modal .ant-card {
    margin-bottom: 16px;
  }

  .analysis-modal .ant-statistic-title {
    font-size: 14px;
    margin-bottom: 8px;
  }

  .analysis-modal .ant-statistic-content {
    font-size: 24px;
    font-weight: bold;
  }
`;

// Inject styles

if (typeof document !== 'undefined') {

  const styleSheet = document.createElement('style');

  styleSheet.textContent = styles;

  document.head.appendChild(styleSheet);

}



export default ResumeUpload;

