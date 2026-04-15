import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { jobsAPI } from '../../services/api';

const styles = `
  .jm-root {
    background: #f0f2f5;
    min-height: 100vh;
    padding: 40px;
    color: #1a1a1a;
  }

  .jm-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
  }

  .jm-title {
    font-size: 28px;
    font-weight: 600;
  }

  .jm-add-btn {
    background: #1677ff;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    cursor: pointer;
  }

  .jm-stats {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
  }

  .jm-card {
    background: #fff;
    border-radius: 10px;
    padding: 16px;
    flex: 1;
  }

  .jm-card-title {
    font-size: 12px;
    color: #999;
  }

  .jm-card-value {
    font-size: 22px;
    font-weight: 600;
  }

  .jm-board {
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
  }

  .jm-header-row, .jm-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 120px;
    padding: 14px 20px;
    align-items: center;
  }

  .jm-header-row {
    background: #fafafa;
    font-size: 12px;
    color: #888;
  }

  .jm-row {
    border-top: 1px solid #f0f0f0;
    cursor: pointer;
  }

  .jm-row:hover {
    background: #f5f7ff;
  }

  .jm-title-text {
    font-weight: 600;
  }

  .jm-company {
    font-size: 13px;
    color: #888;
  }

  .jm-badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
  }

  .blue { background: #e6f4ff; color: #1677ff; }
  .green { background: #f6ffed; color: #52c41a; }
  .orange { background: #fff7e6; color: #fa8c16; }

  .jm-section-title {
    font-weight: 600;
    margin: 20px 0 10px;
  }

  .jm-del {
    border: 1px solid #ffccc7;
    color: #ff4d4f;
    background: none;
    padding: 6px 10px;
    border-radius: 6px;
    cursor: pointer;
  }

  .jm-modal {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.4);
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .jm-modal-box {
    background: white;
    padding: 24px;
    border-radius: 10px;
    width: 300px;
  }

  .jm-modal-actions {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .jm-btn {
    padding: 6px 12px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
  }

  .cancel { background: #f0f0f0; }
  .confirm { background: #ff4d4f; color: white; }
`;

const JobManagement = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmId, setConfirmId] = useState(null);

  const { data: jobs = [] } = useQuery(
    'my-posted-jobs',
    jobsAPI.getMyPostedJobs,
    {
      select: (res) => res?.data?.results || res?.data || [],
    }
  );
  

  

  const deleteMutation = useMutation((id) => jobsAPI.delete(id), {
    onSuccess: () => {
      queryClient.invalidateQueries('my-posted-jobs');
      setConfirmId(null);
    },
  });

  // ✅ FILTER
  const activeJobs = jobs.filter(j => j.is_active === true);
  const closedJobs = jobs.filter(j => j.is_active === false);

  return (
    <>
      <style>{styles}</style>

      <div className="jm-root">

        {/* HEADER */}
        <div className="jm-header">
          <h2 className="jm-title">Job Management</h2>
          <button className="jm-add-btn" onClick={() => navigate('/hr/job-post')}>
            + Add Job
          </button>
        </div>

        {/* STATS */}
        <div className="jm-stats">
          <div className="jm-card">
            <div className="jm-card-title">Total Jobs</div>
            <div className="jm-card-value">{jobs.length}</div>
          </div>
          <div className="jm-card">
            <div className="jm-card-title">Active</div>
            <div className="jm-card-value" style={{ color: '#52c41a' }}>
              {activeJobs.length}
            </div>
          </div>
          <div className="jm-card">
            <div className="jm-card-title">Closed</div>
            <div className="jm-card-value" style={{ color: '#fa8c16' }}>
              {closedJobs.length}
            </div>
          </div>
        </div>

        {/* ACTIVE JOBS */}
        <div className="jm-section-title">Active Jobs</div>
        <div className="jm-board">
          <div className="jm-header-row">
            <div>Position</div>
            <div>Type</div>
            <div>Location</div>
            <div>Status</div>
            <div style={{ textAlign: 'right' }}>Actions</div>
          </div>

          {activeJobs.map(job => (
            <div key={job.id} className="jm-row" onClick={() => navigate(`/hr/job/${job.id}`)}>
              <div>
                <div className="jm-title-text">{job.title}</div>
                <div className="jm-company">{job.company}</div>
              </div>

              <div><span className="jm-badge blue">{job.job_type}</span></div>
              <div>{job.location || '-'}</div>
              <div><span className={`jm-badge ${job.is_active ? 'green' : 'orange'}`}>
                    {job.is_active ? 'active' : 'closed'}
                  </span></div>

              <div>
                <button
                  className="jm-del"
                  onClick={(e) => {
                    e.stopPropagation();
                    setConfirmId(job.id);
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* CLOSED JOBS */}
        <div className="jm-section-title">Closed Jobs</div>
        <div className="jm-board">
          {closedJobs.map(job => (
            <div key={job.id} className="jm-row" onClick={() => navigate(`/hr/job/${job.id}`)}>
              <div>
                <div className="jm-title-text">{job.title}</div>
                <div className="jm-company">{job.company}</div>
              </div>

              <div><span className="jm-badge blue">{job.job_type}</span></div>
              <div>{job.location || '-'}</div>
              <div><span className="jm-badge orange">closed</span></div>

              <div>
                <button
                  className="jm-del"
                  onClick={(e) => {
                    e.stopPropagation();
                    setConfirmId(job.id);
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>

      </div>

      {/* DELETE MODAL */}
      {confirmId && (
        <div className="jm-modal" onClick={() => setConfirmId(null)}>
          <div className="jm-modal-box" onClick={(e) => e.stopPropagation()}>
            <h3>Delete Job?</h3>
            <p>This action cannot be undone.</p>

            <div className="jm-modal-actions">
              <button className="jm-btn cancel" onClick={() => setConfirmId(null)}>
                Cancel
              </button>
              <button
                className="jm-btn confirm"
                onClick={() => deleteMutation.mutate(confirmId)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default JobManagement;