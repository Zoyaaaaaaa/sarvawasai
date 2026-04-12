
// import { useState, useEffect, useRef } from 'react';
// import { Bot, Loader2, Send, Mic, Volume2, Languages, X } from 'lucide-react';

// const HousingSchemeBot = () => {
//   const [messages, setMessages] = useState([
//     {
//       role: 'assistant',
//       content: '🏡 **नमस्ते / Welcome to Housing Scheme Finder!**\n\nI can help you explore housing schemes in India in both Hindi and English.\n\n**मैं आपकी कैसे मदद कर सकता हूं:**\n• Find suitable housing schemes / उपयुक्त आवास योजनाएं खोजें\n• Check eligibility / पात्रता जांचें\n• Get application details / आवेदन विवरण प्राप्त करें\n• Understand documents needed / आवश्यक दस्तावेज समझें\n\nPlease provide your details to get started!'
//     }
//   ]);
//   const [input, setInput] = useState('');
//   const [loading, setLoading] = useState(false);
//   const [isListening, setIsListening] = useState(false);
//   const [isSpeaking, setIsSpeaking] = useState(false);
//   const [language, setLanguage] = useState('en');
//   const [userInfo, setUserInfo] = useState({
//     income: '',
//     category: '',
//     location: '',
//     employment: ''
//   });
//   const [showForm, setShowForm] = useState(true);
//   const messagesEndRef = useRef(null);
//   const recognitionRef = useRef(null);
//   const synthRef = useRef(null);

//   useEffect(() => {
//     // Initialize speech recognition
//     if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
//       const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
//       recognitionRef.current = new SpeechRecognition();
//       recognitionRef.current.continuous = false;
//       recognitionRef.current.interimResults = false;
//       recognitionRef.current.lang = language === 'hi' ? 'hi-IN' : 'en-IN';

//       recognitionRef.current.onresult = (event) => {
//         const transcript = event.results[0][0].transcript;
//         setInput(transcript);
//         setIsListening(false);
//       };

//       recognitionRef.current.onerror = () => {
//         setIsListening(false);
//       };

//       recognitionRef.current.onend = () => {
//         setIsListening(false);
//       };
//     }

//     // Initialize speech synthesis
//     if ('speechSynthesis' in window) {
//       synthRef.current = window.speechSynthesis;
//     }

//     return () => {
//       if (recognitionRef.current) {
//         recognitionRef.current.stop();
//       }
//       if (synthRef.current) {
//         synthRef.current.cancel();
//       }
//     };
//   }, [language]);

//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
//   }, [messages]);

//   const startListening = () => {
//     if (recognitionRef.current && !isListening) {
//       recognitionRef.current.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
//       recognitionRef.current.start();
//       setIsListening(true);
//     }
//   };

//   const stopListening = () => {
//     if (recognitionRef.current && isListening) {
//       recognitionRef.current.stop();
//       setIsListening(false);
//     }
//   };

//   const speakText = (text) => {
//     if (synthRef.current && text) {
//       synthRef.current.cancel();

//       // Remove markdown formatting for speech
//       const cleanText = text
//         .replace(/[#*`_~\[\]()]/g, '')
//         .replace(/\n+/g, '. ')
//         .replace(/\*\*/g, '')
//         .replace(/https?:\/\/[^\s]+/g, 'link');

//       const utterance = new SpeechSynthesisUtterance(cleanText);
//       utterance.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
//       utterance.rate = 0.9;

//       utterance.onstart = () => setIsSpeaking(true);
//       utterance.onend = () => setIsSpeaking(false);
//       utterance.onerror = () => setIsSpeaking(false);

//       synthRef.current.speak(utterance);
//     }
//   };

//   const stopSpeaking = () => {
//     if (synthRef.current) {
//       synthRef.current.cancel();
//       setIsSpeaking(false);
//     }
//   };

//   const toggleLanguage = () => {
//     const newLang = language === 'en' ? 'hi' : 'en';
//     setLanguage(newLang);

//     const langMsg = newLang === 'hi' 
//       ? '🌐 भाषा हिंदी में बदल गई है। मैं अब हिंदी में जवाब दूंगा।'
//       : '🌐 Language switched to English. I will now respond in English.';

//     setMessages(prev => [...prev, {
//       role: 'assistant',
//       content: langMsg
//     }]);
//   };

//   const handleFormSubmit = () => {
//     if (!userInfo.income || !userInfo.category || !userInfo.location || !userInfo.employment) {
//       alert(language === 'hi' ? 'कृपया सभी फील्ड भरें' : 'Please fill all fields');
//       return;
//     }

//     const userMessage = language === 'hi' 
//       ? `मैं आवास योजनाओं की खोज कर रहा हूं। मेरी जानकारी:\n- वार्षिक आय: ₹${userInfo.income}\n- श्रेणी: ${userInfo.category}\n- स्थान: ${userInfo.location}\n- रोजगार स्थिति: ${userInfo.employment}`
//       : `I am searching for housing schemes. My details:\n- Annual Income: ₹${userInfo.income}\n- Category: ${userInfo.category}\n- Location: ${userInfo.location}\n- Employment: ${userInfo.employment}`;

//     setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
//     setShowForm(false);
//     handleBotQuery(userMessage);
//   };

//   const handleBotQuery = async (query) => {
//     setLoading(true);

//     try {
//       const response = await fetch('http://localhost:8000/schemes/chat', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({ 
//           query: query,
//           user_details: userInfo,
//           language: language,
//           conversation_history: messages.slice(-6)
//         })
//       });

//       if (!response.ok) {
//         throw new Error(`Server responded with status: ${response.status}`);
//       }

//       const data = await response.json();

//       const botResponse = {
//         role: 'assistant',
//         content: data.response
//       };

//       setMessages(prev => [...prev, botResponse]);

//       // Auto-speak response
//       if (data.response && !isSpeaking) {
//         setTimeout(() => speakText(data.response), 500);
//       }
//     } catch (error) {
//       console.error('Chat error:', error);
//       const errorMsg = language === 'hi'
//         ? 'क्षमा करें, आवास योजना खोजक से कनेक्ट करने में त्रुटि हुई। कृपया सुनिश्चित करें कि बैकएंड सर्वर चल रहा है और पुनः प्रयास करें।'
//         : 'Sorry, I encountered an error connecting to the housing scheme finder. Please ensure the backend server is running at http://localhost:8000 and try again.';

//       setMessages(prev => [...prev, {
//         role: 'assistant',
//         content: errorMsg
//       }]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleSendMessage = (e) => {
//     if (e) e.preventDefault();
//     if (!input.trim()) return;

//     const userMessage = { role: 'user', content: input };
//     setMessages(prev => [...prev, userMessage]);
//     const query = input;
//     setInput('');

//     handleBotQuery(query);
//   };

//   const handleKeyPress = (e) => {
//     if (e.key === 'Enter' && !e.shiftKey) {
//       e.preventDefault();
//       handleSendMessage(e);
//     }
//   };

//   const renderMarkdown = (text) => {
//     return text
//       .split('\n')
//       .map((line, i) => {
//         // Headers
//         if (line.startsWith('### ')) {
//           return <h3 key={i} className="text-lg font-bold mt-4 mb-2 text-gray-800">{line.replace('### ', '')}</h3>;
//         }
//         if (line.startsWith('## ')) {
//           return <h2 key={i} className="text-xl font-bold mt-4 mb-2 text-gray-900">{line.replace('## ', '')}</h2>;
//         }
//         if (line.startsWith('# ')) {
//           return <h1 key={i} className="text-2xl font-bold mt-4 mb-2 text-gray-900">{line.replace('# ', '')}</h1>;
//         }

//         // Bold text
//         let processedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');

//         // Links
//         processedLine = processedLine.replace(
//           /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
//           '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline font-medium">$1 🔗</a>'
//         );

//         // Bullet points
//         if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
//           return (
//             <li key={i} className="ml-4 mb-1" dangerouslySetInnerHTML={{ __html: processedLine.replace(/^[-•]\s*/, '') }} />
//           );
//         }

//         // Numbered lists
//         if (line.match(/^\d+\.\s/)) {
//           return (
//             <li key={i} className="ml-4 mb-1" dangerouslySetInnerHTML={{ __html: processedLine.replace(/^\d+\.\s*/, '') }} />
//           );
//         }

//         // Regular paragraphs
//         if (line.trim()) {
//           return <p key={i} className="mb-2" dangerouslySetInnerHTML={{ __html: processedLine }} />;
//         }

//         return <br key={i} />;
//       });
//   };

//   const quickActions = language === 'hi' 
//     ? ['आवश्यक दस्तावेज', 'आवेदन प्रक्रिया', 'पात्रता मानदंड', 'योजना लाभ']
//     : ['Required documents', 'Application process', 'Eligibility criteria', 'Scheme benefits'];

//   return (
//     <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
//       <div className="mb-8 flex justify-between items-center">
//         <div>
//           <h2 className="text-3xl font-bold text-gray-900 mb-2">
//             {language === 'hi' ? 'आवास योजना खोजक' : 'Housing Scheme Finder'}
//           </h2>
//           <p className="text-gray-600">
//             {language === 'hi' 
//               ? 'व्यक्तिगत आवास योजना सिफारिशें प्राप्त करें' 
//               : 'Get personalized housing scheme recommendations'}
//           </p>
//         </div>
//         <button
//           onClick={toggleLanguage}
//           className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
//         >
//           <Languages className="w-5 h-5" />
//           <span className="font-medium">{language === 'hi' ? 'English' : 'हिंदी'}</span>
//         </button>
//       </div>

//       <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
//         {showForm && (
//           <div className="p-8 bg-gradient-to-br from-blue-50 to-purple-50 border-b">
//             <h3 className="text-lg font-semibold text-gray-900 mb-6">
//               {language === 'hi' ? 'हमें अपने बारे में बताएं' : 'Tell us about yourself'}
//             </h3>
//             <div className="grid md:grid-cols-2 gap-4">
//               <input
//                 type="text"
//                 placeholder={language === 'hi' ? 'वार्षिक आय (जैसे, 500000)' : 'Annual Income (e.g., 500000)'}
//                 value={userInfo.income}
//                 onChange={(e) => setUserInfo({...userInfo, income: e.target.value})}
//                 className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               />
//               <select
//                 value={userInfo.category}
//                 onChange={(e) => setUserInfo({...userInfo, category: e.target.value})}
//                 className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               >
//                 <option value="">{language === 'hi' ? 'श्रेणी चुनें' : 'Select Category'}</option>
//                 <option value="General">General / सामान्य</option>
//                 <option value="OBC">OBC / अन्य पिछड़ा वर्ग</option>
//                 <option value="SC">SC / अनुसूचित जाति</option>
//                 <option value="ST">ST / अनुसूचित जनजाति</option>
//                 <option value="EWS">EWS / आर्थिक रूप से कमजोर वर्ग</option>
//               </select>
//               <input
//                 type="text"
//                 placeholder={language === 'hi' ? 'राज्य या शहर' : 'State or City'}
//                 value={userInfo.location}
//                 onChange={(e) => setUserInfo({...userInfo, location: e.target.value})}
//                 className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               />
//               <select
//                 value={userInfo.employment}
//                 onChange={(e) => setUserInfo({...userInfo, employment: e.target.value})}
//                 className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               >
//                 <option value="">{language === 'hi' ? 'रोजगार स्थिति' : 'Employment Status'}</option>
//                 <option value="Employed">{language === 'hi' ? 'नियोजित' : 'Employed'}</option>
//                 <option value="Self-employed">{language === 'hi' ? 'स्व-नियोजित' : 'Self-employed'}</option>
//                 <option value="Unemployed">{language === 'hi' ? 'बेरोजगार' : 'Unemployed'}</option>
//               </select>
//             </div>
//             <button
//               onClick={handleFormSubmit}
//               className="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
//             >
//               {language === 'hi' ? 'योजनाएं खोजें' : 'Find Schemes'}
//             </button>
//           </div>
//         )}

//         <div className="h-96 overflow-y-auto p-6 space-y-4">
//           {messages.map((msg, idx) => (
//             <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
//               <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
//                 msg.role === 'user' 
//                   ? 'bg-blue-600 text-white' 
//                   : 'bg-gray-50 text-gray-900 border border-gray-200'
//               }`}>
//                 {msg.role === 'assistant' && (
//                   <div className="flex items-center justify-between mb-2">
//                     <Bot className="w-5 h-5 text-blue-600" />
//                     <button
//                       onClick={() => isSpeaking ? stopSpeaking() : speakText(msg.content)}
//                       className="p-1 hover:bg-gray-200 rounded transition-colors"
//                       title={isSpeaking ? 'Stop' : 'Listen'}
//                     >
//                       {isSpeaking ? (
//                         <X className="w-4 h-4 text-red-600" />
//                       ) : (
//                         <Volume2 className="w-4 h-4 text-blue-600" />
//                       )}
//                     </button>
//                   </div>
//                 )}
//                 <div className="text-sm leading-relaxed">
//                   {msg.role === 'assistant' ? renderMarkdown(msg.content) : msg.content}
//                 </div>
//               </div>
//             </div>
//           ))}
//           {loading && (
//             <div className="flex justify-start">
//               <div className="bg-gray-50 rounded-2xl px-4 py-3 border border-gray-200">
//                 <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
//               </div>
//             </div>
//           )}
//           <div ref={messagesEndRef} />
//         </div>

//         <div className="p-4 border-t bg-gray-50">
//           <div className="flex gap-3">
//             <input
//               type="text"
//               value={input}
//               onChange={(e) => setInput(e.target.value)}
//               onKeyPress={handleKeyPress}
//               placeholder={language === 'hi' 
//                 ? 'योजनाओं, पात्रता, दस्तावेजों के बारे में पूछें...' 
//                 : 'Ask about schemes, eligibility, documents...'}
//               className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               disabled={loading}
//             />
//             <button
//               onClick={isListening ? stopListening : startListening}
//               className={`px-4 py-3 rounded-lg font-medium transition-colors ${
//                 isListening 
//                   ? 'bg-red-600 text-white hover:bg-red-700 animate-pulse' 
//                   : 'bg-purple-600 text-white hover:bg-purple-700'
//               }`}
//               disabled={loading}
//             >
//               <Mic className="w-5 h-5" />
//             </button>
//             <button
//               onClick={handleSendMessage}
//               disabled={loading}
//               className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
//             >
//               <Send className="w-5 h-5" />
//             </button>
//           </div>
//         </div>
//       </div>

//       {!showForm && (
//         <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
//           {quickActions.map((action, idx) => (
//             <button
//               key={idx}
//               onClick={() => setInput(action)}
//               className="px-4 py-2 bg-white border-2 border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:border-blue-600 hover:text-blue-600 transition-colors"
//             >
//               {action}
//             </button>
//           ))}
//         </div>
//       )}

//       <div className="mt-8 grid md:grid-cols-3 gap-4">
//         <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
//           <h4 className="font-semibold text-gray-900 mb-2">
//             {language === 'hi' ? 'पीएमएवाई' : 'PMAY'}
//           </h4>
//           <p className="text-sm text-gray-600">
//             {language === 'hi' 
//               ? 'प्रधानमंत्री आवास योजना - केंद्र सरकार की योजना' 
//               : 'Pradhan Mantri Awas Yojana - Central Government Scheme'}
//           </p>
//         </div>
//         <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
//           <h4 className="font-semibold text-gray-900 mb-2">
//             {language === 'hi' ? 'राज्य योजनाएं' : 'State Schemes'}
//           </h4>
//           <p className="text-sm text-gray-600">
//             {language === 'hi' 
//               ? 'स्थान-विशिष्ट आवास लाभ' 
//               : 'Location-specific housing benefits'}
//           </p>
//         </div>
//         <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
//           <h4 className="font-semibold text-gray-900 mb-2">
//             {language === 'hi' ? 'श्रेणी लाभ' : 'Category Benefits'}
//           </h4>
//           <p className="text-sm text-gray-600">
//             {language === 'hi' 
//               ? 'SC/ST/OBC/EWS के लिए विशेष प्रावधान' 
//               : 'Special provisions for SC/ST/OBC/EWS'}
//           </p>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default HousingSchemeBot;

import { useState, useEffect, useRef } from 'react';
import { Bot, Loader2, Send, Mic, Volume2, Languages, X, MicOff, VolumeX } from 'lucide-react';
import { apiUrl } from '@/lib/api.js';

const titleClass = 'heading-2 tracking-tight text-gray-900';
const subtitleClass = 'body-sm text-gray-600';
const fieldClass = 'w-full flex-1 min-w-0 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 shadow-sm transition-all placeholder:text-gray-400 focus:border-accent-purple focus:outline-none focus:ring-2 focus:ring-[rgba(88,28,135,0.14)]';
const primaryButtonClass = 'mt-6 w-full rounded-xl bg-accent-purple px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50';
const sendButtonClass = 'inline-flex items-center justify-center rounded-xl bg-accent-blue px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50';
const outlineButtonClass = 'inline-flex items-center justify-center rounded-xl border-2 border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm transition-colors hover:border-accent-blue hover:text-accent-blue';
const modeButtonClass = 'flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors';
const bubbleClass = 'max-w-[85%] rounded-2xl px-4 py-3 shadow-sm';
const assistantBubbleClass = 'border border-gray-200 bg-white text-gray-900';
const userBubbleClass = 'bg-accent-purple text-white';
const linkClass = 'text-accent-blue hover:opacity-80 underline font-medium';

const HousingSchemeBot = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '🏡 **नमस्ते / Welcome to Housing Scheme Finder!**\n\nI can help you explore housing schemes in India in both Hindi and English.\n\n**मैं आपकी कैसे मदद कर सकता हूं:**\n• Find suitable housing schemes / उपयुक्त आवास योजनाएं खोजें\n• Check eligibility / पात्रता जांचें\n• Get application details / आवेदन विवरण प्राप्त करें\n• Understand documents needed / आवश्यक दस्तावेज समझें\n\nPlease provide your details to get started!'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [language, setLanguage] = useState('en');
  const [sessionId, setSessionId] = useState('');
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [userInfo, setUserInfo] = useState({
    income: '',
    category: '',
    location: '',
    employment: ''
  });
  const [showForm, setShowForm] = useState(true);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const currentAudioRef = useRef(null);

  useEffect(() => {
    // Generate session ID
    setSessionId(`session_${Date.now()}`);

    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = language === 'hi' ? 'hi-IN' : 'en-IN';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      stopAudio();
    };
  }, [language]);

  useEffect(() => {
    // Only scroll to bottom if there are multiple messages (user has interacted)
    if (messages.length > 1) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      recognitionRef.current.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const stopAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    setIsSpeaking(false);
  };

  const speakTextWithTTS = async (text) => {
    if (!audioEnabled || !text) return;

    try {
      stopAudio();
      setIsSpeaking(true);

      // Remove markdown formatting for speech
      const cleanText = text
        .replace(/[#*`_~\[\]()]/g, '')
        .replace(/\n+/g, '. ')
        .replace(/\*\*/g, '')
        .replace(/https?:\/\/[^\s]+/g, '');

      // Call TTS API
      const response = await fetch(apiUrl('/schemes/tts'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: cleanText,
          style: 'Conversational',
          rate: 0,
          pitch: 0,
          variation: 1
        })
      });

      if (!response.ok) {
        throw new Error('TTS request failed');
      }

      // Get audio blob
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      // Play audio
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;

      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
      };

      audio.onerror = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
      };

      await audio.play();
    } catch (error) {
      console.error('TTS Error:', error);
      setIsSpeaking(false);
    }
  };

  const toggleLanguage = async () => {
    const newLang = language === 'en' ? 'hi' : 'en';
    setLanguage(newLang);

    const langMsg = newLang === 'hi'
      ? '🌐 भाषा हिंदी में बदल गई है। मैं अब हिंदी में जवाब दूंगा।'
      : '🌐 Language switched to English. I will now respond in English.';

    setMessages(prev => [...prev, {
      role: 'assistant',
      content: langMsg
    }]);

    // Detect language via API
    try {
      const response = await fetch(apiUrl('/schemes/detect-language'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: langMsg })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Detected language:', data);
      }
    } catch (error) {
      console.error('Language detection error:', error);
    }
  };

  const handleFormSubmit = () => {
    if (!userInfo.income || !userInfo.category || !userInfo.location || !userInfo.employment) {
      alert(language === 'hi' ? 'कृपया सभी फील्ड भरें' : 'Please fill all fields');
      return;
    }

    const userMessage = language === 'hi'
      ? `मैं आवास योजनाओं की खोज कर रहा हूं। मेरी जानकारी:\n- वार्षिक आय: ₹${userInfo.income}\n- श्रेणी: ${userInfo.category}\n- स्थान: ${userInfo.location}\n- रोजगार स्थिति: ${userInfo.employment}`
      : `I am searching for housing schemes. My details:\n- Annual Income: ₹${userInfo.income}\n- Category: ${userInfo.category}\n- Location: ${userInfo.location}\n- Employment: ${userInfo.employment}`;

    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setShowForm(false);
    handleBotQuery(userMessage);
  };

  const handleBotQuery = async (query) => {
    setLoading(true);

    try {
      // Use the unified /chat endpoint
      const endpoint = apiUrl('/schemes/chat');

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          user_details: userInfo,
          language: language,
          session_id: sessionId,
          return_audio: audioEnabled
        })
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();

      const botResponse = {
        role: 'assistant',
        content: data.response
      };

      setMessages(prev => [...prev, botResponse]);

      // Play audio if available (from audio_base64)
      if (audioEnabled && data.audio_base64) {
        try {
          // Decode base64 audio
          const binaryString = atob(data.audio_base64);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const audioBlob = new Blob([bytes], { type: 'audio/wav' });
          const audioUrl = URL.createObjectURL(audioBlob);

          const audio = new Audio(audioUrl);
          currentAudioRef.current = audio;
          setIsSpeaking(true);

          audio.onended = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            currentAudioRef.current = null;
          };

          audio.onerror = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            currentAudioRef.current = null;
          };

          await audio.play();
        } catch (audioError) {
          console.error('Audio playback error:', audioError);
          // Fallback to separate TTS API if needed
          if (data.response) {
            setTimeout(() => speakTextWithTTS(data.response), 500);
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg = language === 'hi'
        ? 'क्षमा करें, आवास योजना खोजक से कनेक्ट करने में त्रुटि हुई। कृपया सुनिश्चित करें कि बैकएंड सर्वर चल रहा है और पुनः प्रयास करें।'
        : 'Sorry, I encountered an error connecting to the housing scheme finder. Please ensure the backend server is running and try again.';

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: errorMsg
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = (e) => {
    if (e) e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    const query = input;
    setInput('');

    handleBotQuery(query);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const renderMarkdown = (text) => {
    return text
      .split('\n')
      .map((line, i) => {
        // Headers
        if (line.startsWith('### ')) {
          return <h3 key={i} className="heading-4 mt-4 mb-2 text-gray-800">{line.replace('### ', '')}</h3>;
        }
        if (line.startsWith('## ')) {
          return <h2 key={i} className="heading-3 mt-4 mb-2">{line.replace('## ', '')}</h2>;
        }
        if (line.startsWith('# ')) {
          return <h1 key={i} className="heading-2 mt-4 mb-2">{line.replace('# ', '')}</h1>;
        }

        // Bold text
        let processedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');

        // Links
        processedLine = processedLine.replace(
          /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
          `<a href="$2" target="_blank" rel="noopener noreferrer" class="${linkClass}">$1 🔗</a>`
        );

        // Bullet points
        if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
          return (
            <li key={i} className="ml-4 mb-1 body-sm" dangerouslySetInnerHTML={{ __html: processedLine.replace(/^[-•]\s*/, '') }} />
          );
        }

        // Numbered lists
        if (line.match(/^\d+\.\s/)) {
          return (
            <li key={i} className="ml-4 mb-1 body-sm" dangerouslySetInnerHTML={{ __html: processedLine.replace(/^\d+\.\s*/, '') }} />
          );
        }

        // Regular paragraphs
        if (line.trim()) {
          return <p key={i} className="mb-2 body-base" dangerouslySetInnerHTML={{ __html: processedLine }} />;
        }

        return <br key={i} />;
      });
  };

  const quickActions = language === 'hi'
    ? ['आवश्यक दस्तावेज', 'आवेदन प्रक्रिया', 'पात्रता मानदंड', 'योजना लाभ']
    : ['Required documents', 'Application process', 'Eligibility criteria', 'Scheme benefits'];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8 flex flex-col gap-4 rounded-3xl border border-gray-200 bg-white px-6 py-6 shadow-sm sm:flex-row sm:items-start sm:justify-between sm:px-8">
        <div>
          <h1 className={titleClass}>
            {language === 'hi' ? 'आवास योजना खोजक' : 'Housing Scheme Finder'}
          </h1>
          <p className={subtitleClass}>
            {language === 'hi'
              ? 'व्यक्तिगत आवास योजना सिफारिशें प्राप्त करें'
              : 'Get personalized housing scheme recommendations'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className={`${modeButtonClass} ${audioEnabled
                ? 'bg-emerald-600 hover:bg-emerald-700'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            title={audioEnabled ? 'Audio Enabled' : 'Audio Disabled'}
          >
            {audioEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
          </button>
          <button
            onClick={toggleLanguage}
            className={`${modeButtonClass} bg-accent-purple hover:opacity-95`}
          >
            <Languages className="w-5 h-5" />
            <span>{language === 'hi' ? 'English' : 'हिंदी'}</span>
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-md">
        {showForm && (
          <div className="border-b border-gray-100 bg-gradient-to-br from-white to-[#F8FAFF] p-8">
            <h3 className="mb-6 text-lg font-semibold text-gray-900">
              {language === 'hi' ? 'हमें अपने बारे में बताएं' : 'Tell us about yourself'}
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder={language === 'hi' ? 'वार्षिक आय (जैसे, 500000)' : 'Annual Income (e.g., 500000)'}
                value={userInfo.income}
                onChange={(e) => setUserInfo({ ...userInfo, income: e.target.value })}
                className={fieldClass}
              />
              <select
                value={userInfo.category}
                onChange={(e) => setUserInfo({ ...userInfo, category: e.target.value })}
                className={fieldClass}
              >
                <option value="">{language === 'hi' ? 'श्रेणी चुनें' : 'Select Category'}</option>
                <option value="General">General / सामान्य</option>
                <option value="OBC">OBC / अन्य पिछड़ा वर्ग</option>
                <option value="SC">SC / अनुसूचित जाति</option>
                <option value="ST">ST / अनुसूचित जनजाति</option>
                <option value="EWS">EWS / आर्थिक रूप से कमजोर वर्ग</option>
              </select>
              <input
                type="text"
                placeholder={language === 'hi' ? 'राज्य या शहर' : 'State or City'}
                value={userInfo.location}
                onChange={(e) => setUserInfo({ ...userInfo, location: e.target.value })}
                className={fieldClass}
              />
              <select
                value={userInfo.employment}
                onChange={(e) => setUserInfo({ ...userInfo, employment: e.target.value })}
                className={fieldClass}
              >
                <option value="">{language === 'hi' ? 'रोजगार स्थिति' : 'Employment Status'}</option>
                <option value="Employed">{language === 'hi' ? 'नियोजित' : 'Employed'}</option>
                <option value="Self-employed">{language === 'hi' ? 'स्व-नियोजित' : 'Self-employed'}</option>
                <option value="Unemployed">{language === 'hi' ? 'बेरोजगार' : 'Unemployed'}</option>
              </select>
            </div>
            <button
              onClick={handleFormSubmit}
              className={primaryButtonClass}
            >
              {language === 'hi' ? 'योजनाएं खोजें' : 'Find Schemes'}
            </button>
          </div>
        )}

        <div className="h-96 overflow-y-auto bg-[#FAFAFC] p-6 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`${bubbleClass} ${msg.role === 'user'
                  ? userBubbleClass
                  : assistantBubbleClass
                }`}>
                {msg.role === 'assistant' && (
                  <div className="flex items-center justify-between mb-2">
                    <Bot className="w-5 h-5 text-accent-blue" />
                    {audioEnabled && (
                      <button
                        onClick={() => isSpeaking ? stopAudio() : speakTextWithTTS(msg.content)}
                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                        title={isSpeaking ? 'Stop' : 'Listen'}
                      >
                        {isSpeaking ? (
                          <X className="w-4 h-4 text-red-600" />
                        ) : (
                          <Volume2 className="w-4 h-4 text-accent-blue" />
                        )}
                      </button>
                    )}
                  </div>
                )}
                <div className="text-sm leading-relaxed">
                  {msg.role === 'assistant' ? renderMarkdown(msg.content) : msg.content}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
                <Loader2 className="w-5 h-5 animate-spin text-accent-blue" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-gray-100 bg-white p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={language === 'hi'
                ? 'योजनाओं, पात्रता, दस्तावेजों के बारे में पूछें...'
                : 'Ask about schemes, eligibility, documents...'}
              className={fieldClass}
              disabled={loading}
            />
            <button
              onClick={isListening ? stopListening : startListening}
              className={`px-4 py-3 rounded-lg font-medium transition-colors ${isListening
                  ? 'bg-red-600 text-white hover:bg-red-700 animate-pulse'
                  : 'bg-accent-purple text-white hover:opacity-95'
                }`}
              disabled={loading}
              title={isListening ? 'Stop Recording' : 'Start Voice Input'}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>
            <button
              onClick={handleSendMessage}
              disabled={loading}
              className={sendButtonClass}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          {isSpeaking && (
            <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
              <Volume2 className="w-4 h-4 animate-pulse text-accent-blue" />
              <span>{language === 'hi' ? 'बोल रहा है...' : 'Speaking...'}</span>
            </div>
          )}
        </div>
      </div>

      {!showForm && (
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
          {quickActions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => setInput(action)}
              className={outlineButtonClass}
            >
              {action}
            </button>
          ))}
        </div>
      )}

      <div className="mt-8 grid md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
          <h4 className="font-semibold text-gray-900 mb-2">
            {language === 'hi' ? 'पीएमएवाई' : 'PMAY'}
          </h4>
          <p className="text-sm text-gray-600">
            {language === 'hi'
              ? 'प्रधानमंत्री आवास योजना - केंद्र सरकार की योजना'
              : 'Pradhan Mantri Awas Yojana - Central Government Scheme'}
          </p>
        </div>
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
          <h4 className="font-semibold text-gray-900 mb-2">
            {language === 'hi' ? 'राज्य योजनाएं' : 'State Schemes'}
          </h4>
          <p className="text-sm text-gray-600">
            {language === 'hi'
              ? 'स्थान-विशिष्ट आवास लाभ'
              : 'Location-specific housing benefits'}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
          <h4 className="font-semibold text-gray-900 mb-2">
            {language === 'hi' ? 'श्रेणी लाभ' : 'Category Benefits'}
          </h4>
          <p className="text-sm text-gray-600">
            {language === 'hi'
              ? 'SC/ST/OBC/EWS के लिए विशेष प्रावधान'
              : 'Special provisions for SC/ST/OBC/EWS'}
          </p>
        </div>
      </div>

      <div className="mt-4 text-center text-xs text-gray-500">
        Session ID: {sessionId} | Audio: {audioEnabled ? 'Enabled' : 'Disabled'} | Language: {language.toUpperCase()}
      </div>
    </div>
  );
};

export default HousingSchemeBot;
