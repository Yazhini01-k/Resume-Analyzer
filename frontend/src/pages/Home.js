import React from "react";
import { Button, Typography, Row, Col } from "antd";
import { useNavigate } from "react-router-dom";

const { Title, Paragraph } = Typography;

const Home = () => {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: "100vh", background: "#f5f7fa" }}>
      
      {/* Top Navbar */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        padding: "20px 60px",
        background: "#ffffff",
        boxShadow: "0 2px 8px rgba(0,0,0,0.05)"
      }}>
        <Title level={4} style={{ margin: 0 }}>
          Resume Analyzer
        </Title>

        <div>
          <Button 
            type="link" 
            onClick={() => navigate("/login")}
            style={{ marginRight: 10 }}
          >
            Sign In
          </Button>
          <Button 
            type="primary" 
            onClick={() => navigate("/register")}
          >
            Sign Up
          </Button>
        </div>
      </div>

      {/* Hero Section */}
      <Row justify="center" align="middle" style={{ height: "80vh" }}>
        <Col span={12} style={{ textAlign: "center" }}>
          <Title>AI Powered Resume Analyzer</Title>
          <Paragraph style={{ fontSize: 18 }}>
            Upload your resume. Get instant feedback. Improve your chances.
          </Paragraph>
          <Button 
            type="primary" 
            size="large"
            onClick={() => navigate("/register")}
          >
            Get Started
          </Button>
        </Col>
      </Row>
    </div>
  );
};

export default Home;