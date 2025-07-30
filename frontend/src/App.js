import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";
import { 
  PlusIcon, 
  SparklesIcon, 
  LightBulbIcon,
  CogIcon,
  EyeIcon,
  WrenchIcon,
  UserIcon,
  HomeIcon,
  XMarkIcon
} from "@heroicons/react/24/outline";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Stages configuration
const STAGES = [
  { id: "suggested", name: "Suggested", icon: SparklesIcon, color: "purple", description: "Fresh AI-generated ideas" },
  { id: "deep_dive", name: "Deep Dive", icon: LightBulbIcon, color: "blue", description: "Exploring potential" },
  { id: "iterating", name: "Iterating", icon: CogIcon, color: "yellow", description: "Refining the concept" },
  { id: "considering", name: "Considering", icon: EyeIcon, color: "green", description: "Evaluating feasibility" },
  { id: "building", name: "Building", icon: WrenchIcon, color: "red", description: "Ready for development" }
];

// Home Component
const Home = () => {
  const [currentUser, setCurrentUser] = useState(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIdea, setSelectedIdea] = useState(null);
  const [feedback, setFeedback] = useState("");

  const [profileForm, setProfileForm] = useState({
    name: "",
    background: "",
    experience: "",
    interests: "",
    skills: ""
  });

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/profiles`);
      if (response.data.length > 0) {
        setCurrentUser(response.data[0]);
        loadUserIdeas(response.data[0].id);
      }
    } catch (error) {
      console.error("Error loading profile:", error);
    }
  };

  const loadUserIdeas = async (userId) => {
    try {
      const response = await axios.get(`${API}/ideas/user/${userId}`);
      setIdeas(response.data);
    } catch (error) {
      console.error("Error loading ideas:", error);
    }
  };

  const createProfile = async () => {
    try {
      const profileData = {
        name: profileForm.name,
        background: profileForm.background,
        experience: profileForm.experience.split(',').map(item => item.trim()),
        interests: profileForm.interests.split(',').map(item => item.trim()),
        skills: profileForm.skills.split(',').map(item => item.trim())
      };

      const response = await axios.post(`${API}/profiles`, profileData);
      setCurrentUser(response.data);
      setShowProfileModal(false);
      setProfileForm({ name: "", background: "", experience: "", interests: "", skills: "" });
    } catch (error) {
      console.error("Error creating profile:", error);
    }
  };

  const generateAIIdeas = async () => {
    if (!currentUser) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/ideas/generate`, {
        user_id: currentUser.id,
        count: 5
      });
      
      await loadUserIdeas(currentUser.id);
    } catch (error) {
      console.error("Error generating ideas:", error);
    } finally {
      setLoading(false);
    }
  };

  const getAIFeedback = async (ideaId, stage) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/ideas/feedback`, {
        idea_id: ideaId,
        stage: stage
      });
      
      setFeedback(response.data.feedback);
      await loadUserIdeas(currentUser.id);
    } catch (error) {
      console.error("Error getting feedback:", error);
    } finally {
      setLoading(false);
    }
  };

  const onDragEnd = async (result) => {
    if (!result.destination) return;

    const { draggableId, destination } = result;
    const newStage = destination.droppableId;
    
    try {
      await axios.put(`${API}/ideas/${draggableId}`, {
        stage: newStage
      });
      
      await loadUserIdeas(currentUser.id);
    } catch (error) {
      console.error("Error updating idea stage:", error);
    }
  };

  const getIdeasByStage = (stage) => {
    return ideas.filter(idea => idea.stage === stage);
  };

  const StageIcon = ({ stage }) => {
    const stageConfig = STAGES.find(s => s.id === stage);
    const IconComponent = stageConfig?.icon || SparklesIcon;
    return <IconComponent className="h-5 w-5" />;
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-4">
          <div className="text-center mb-6">
            <div className="mx-auto w-16 h-16 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full flex items-center justify-center mb-4">
              <SparklesIcon className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome to ID8</h1>
            <p className="text-gray-600">GitHub for Ideas - Transform your sparks into funded products</p>
          </div>
          
          <button
            onClick={() => setShowProfileModal(true)}
            className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-3 px-6 rounded-xl font-semibold hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Create Your Profile
          </button>
        </div>

        {/* Profile Modal */}
        {showProfileModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-90vh overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Create Your Profile</h2>
                  <button
                    onClick={() => setShowProfileModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Name</label>
                    <input
                      type="text"
                      value={profileForm.name}
                      onChange={(e) => setProfileForm({...profileForm, name: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Your full name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Background</label>
                    <textarea
                      value={profileForm.background}
                      onChange={(e) => setProfileForm({...profileForm, background: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent h-24"
                      placeholder="Tell us about your professional background..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Experience (comma-separated)</label>
                    <input
                      type="text"
                      value={profileForm.experience}
                      onChange={(e) => setProfileForm({...profileForm, experience: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Software development, Marketing, Design..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Interests (comma-separated)</label>
                    <input
                      type="text"
                      value={profileForm.interests}
                      onChange={(e) => setProfileForm({...profileForm, interests: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="AI, Sustainability, Education, Gaming..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Skills (comma-separated)</label>
                    <input
                      type="text"
                      value={profileForm.skills}
                      onChange={(e) => setProfileForm({...profileForm, skills: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Python, React, Project Management..."
                    />
                  </div>
                </div>

                <div className="flex gap-4 mt-8">
                  <button
                    onClick={() => setShowProfileModal(false)}
                    className="flex-1 bg-gray-200 text-gray-800 py-3 px-6 rounded-xl font-semibold hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={createProfile}
                    disabled={!profileForm.name || !profileForm.background}
                    className="flex-1 bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-3 px-6 rounded-xl font-semibold hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Create Profile
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
                <SparklesIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">ID8</h1>
                <p className="text-sm text-gray-600">GitHub for Ideas</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <UserIcon className="h-5 w-5 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">{currentUser.name}</span>
              </div>
              
              <button
                onClick={generateAIIdeas}
                disabled={loading}
                className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-4 py-2 rounded-xl font-semibold hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center space-x-2 disabled:opacity-50"
              >
                <SparklesIcon className="h-4 w-4" />
                <span>{loading ? 'Generating...' : 'Generate Ideas'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          {STAGES.map((stage) => {
            const stageIdeas = getIdeasByStage(stage.id);
            return (
              <div key={stage.id} className={`stats-card stats-card-${stage.color} p-4 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200 hover:-translate-y-1`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stage.name}</p>
                    <p className="text-2xl font-bold text-gray-900">{stageIdeas.length}</p>
                  </div>
                  <stage.icon className={`h-8 w-8 text-${stage.color}-500`} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Kanban Board */}
        <DragDropContext onDragEnd={onDragEnd}>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {STAGES.map((stage) => (
              <div key={stage.id} className="bg-white rounded-2xl shadow-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <stage.icon className={`h-5 w-5 text-${stage.color}-500`} />
                    <h3 className="font-semibold text-gray-900">{stage.name}</h3>
                    <span className={`bg-${stage.color}-100 text-${stage.color}-800 text-xs font-medium px-2 py-1 rounded-full`}>
                      {getIdeasByStage(stage.id).length}
                    </span>
                  </div>
                </div>
                
                <p className="text-xs text-gray-500 mb-4">{stage.description}</p>

                <Droppable droppableId={stage.id}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className={`min-h-96 space-y-3 ${snapshot.isDraggingOver ? 'bg-purple-50 rounded-xl' : ''}`}
                    >
                      {getIdeasByStage(stage.id).map((idea, index) => (
                        <Draggable key={idea.id} draggableId={idea.id} index={index}>
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className={`bg-gradient-to-r from-purple-50 to-indigo-50 p-4 rounded-xl border border-purple-100 hover:shadow-lg transition-all duration-200 cursor-pointer ${snapshot.isDragging ? 'shadow-2xl transform rotate-2' : ''}`}
                              onClick={() => setSelectedIdea(idea)}
                            >
                              <h4 className="font-semibold text-gray-900 mb-2 line-clamp-2">{idea.title}</h4>
                              <p className="text-sm text-gray-600 mb-3 line-clamp-3">{idea.description}</p>
                              
                              <div className="flex items-center justify-between">
                                <div className="flex flex-wrap gap-1">
                                  {idea.tags.slice(0, 2).map((tag, index) => (
                                    <span key={index} className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                                
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    getAIFeedback(idea.id, idea.stage);
                                  }}
                                  className="text-purple-500 hover:text-purple-700 text-xs font-medium"
                                >
                                  Get AI Feedback
                                </button>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            ))}
          </div>
        </DragDropContext>
      </div>

      {/* Idea Detail Modal */}
      {selectedIdea && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-90vh overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-center space-x-3">
                  <StageIcon stage={selectedIdea.stage} />
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{selectedIdea.title}</h2>
                    <p className="text-sm text-gray-600 capitalize">{selectedIdea.stage.replace('_', ' ')}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedIdea(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                  <p className="text-gray-700 leading-relaxed">{selectedIdea.description}</p>
                </div>

                {selectedIdea.tags.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Tags</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedIdea.tags.map((tag, index) => (
                        <span key={index} className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedIdea.ai_feedback && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">AI Feedback</h3>
                    <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-4 rounded-xl border border-purple-100">
                      <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{selectedIdea.ai_feedback}</p>
                    </div>
                  </div>
                )}

                <div className="flex gap-4">
                  <button
                    onClick={() => getAIFeedback(selectedIdea.id, selectedIdea.stage)}
                    disabled={loading}
                    className="flex-1 bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-2 px-4 rounded-xl font-semibold hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50"
                  >
                    {loading ? 'Getting Feedback...' : 'Refresh AI Feedback'}
                  </button>
                  <button
                    onClick={() => setSelectedIdea(null)}
                    className="px-6 py-2 bg-gray-200 text-gray-800 rounded-xl font-semibold hover:bg-gray-300 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Modal */}
      {feedback && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">AI Feedback</h3>
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-4 rounded-xl border border-purple-100 mb-6">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{feedback}</p>
              </div>
              <button
                onClick={() => setFeedback("")}
                className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-2 px-4 rounded-xl font-semibold hover:from-purple-600 hover:to-indigo-700 transition-all duration-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;