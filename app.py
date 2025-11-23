import streamlit as st
from streamlit_chat import message
from logger_utils import log_error

from ai_agent import ProcurementAssistant
from data_explorer import DataExplorer

st.set_page_config(
    page_title="CA Procurement Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .example-query {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
        cursor: pointer;
        border-left: 3px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_assistant():
    try:
        return ProcurementAssistant()
    except Exception as e:
        st.error(f"Failed to initialize assistant: {e}")
        st.stop()

@st.cache_resource
def get_explorer():
    try:
        return DataExplorer()
    except Exception as e:
        st.error(f"Failed to initialize data explorer: {e}")
        return None

@st.cache_data(ttl=300)
def get_overview_data():
    try:
        explorer = get_explorer()
        if explorer:
            return explorer.get_overview()
        return None
    except Exception as e:
        log_error(f"Error getting overview: {e}")
        return None

def display_sidebar():
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3db.png", width=80)
        st.title("Procurement Assistant")
        
        st.markdown("---")
        
        st.subheader("📊 Dataset Overview")
        
        overview = get_overview_data()
        if overview:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Records", f"{overview['total_records']:,}")
                st.metric("Departments", f"{overview['departments']:,}")
            with col2:
                if 'total_spending' in overview:
                    st.metric("Total Spending", f"${overview['total_spending']/1e9:.2f}B")
                st.metric("Suppliers", f"{overview['suppliers']:,}")
            
            with st.expander("Fiscal Years"):
                for fy in sorted(overview['fiscal_years']):
                    st.write(f"• {fy}")
        else:
            st.warning("Could not load dataset overview")
        
        st.markdown("---")
        
        st.subheader("💡 Example Queries")
        st.markdown("""
Try asking questions like:
        
**Spending Analysis:**
- What was the total spending in 2013-2014?
- Which quarter had the highest spending?
- Show me spending trends by fiscal year

**Orders & Items:**
- How many orders were created in Q2 2014?
- What are the most frequently ordered items?
- Show me the largest purchase orders

**Departments & Suppliers:**
- Which department spent the most?
- Who are the top 5 suppliers by spending?
- List departments that used CalCard

**Specific Searches:**
- Find all IT goods purchases over $100,000
- Show me orders from a specific department
- What acquisition methods are most common?
        """)

def display_main_content():
    st.markdown('<div class="main-header">🏛️ California Procurement Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Ask questions about California state procurement data in natural language</div>',
        unsafe_allow_html=True
    )
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        st.session_state.assistant = get_assistant()
        st.session_state.pending_query = None
    
    col1, col2, col3, col4 = st.columns(4)
    
    quick_queries = [
        "Total spending by year",
        "Highest spending quarter",
        "Top 5 items ordered",
        "Top 10 departments"
    ]
    
    clicked_query = None
    with col1:
        if st.button(quick_queries[0], use_container_width=True):
            clicked_query = "What was the total spending for each fiscal year?"
    with col2:
        if st.button(quick_queries[1], use_container_width=True):
            clicked_query = "Which quarter had the highest spending across all years?"
    with col3:
        if st.button(quick_queries[2], use_container_width=True):
            clicked_query = "What are the top 5 most frequently ordered items?"
    with col4:
        if st.button(quick_queries[3], use_container_width=True):
            clicked_query = "Which are the top 10 departments by total spending?"
    
    st.markdown("---")
    
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            message(msg["content"], is_user=True, key=f"user_{i}")
        elif msg["role"] == "assistant":
            message(msg["content"], is_user=False, key=f"assistant_{i}")
    
    user_input = st.chat_input("Ask a question about the procurement data...")
    
    if clicked_query:
        user_input = clicked_query
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.pending_query = user_input
        st.rerun()
    
    if hasattr(st.session_state, 'pending_query') and st.session_state.pending_query:
        query = st.session_state.pending_query
        del st.session_state.pending_query
        
        typing_placeholder = st.empty()
        typing_placeholder.markdown("""
        <div style="display: flex; align-items: center; padding: 10px; margin: 10px 0;">
            <div style="background: #f0f2f6; padding: 12px 16px; border-radius: 18px; display: inline-block;">
                <span style="color: #666;">Thinking</span>
                <span class="typing-dots" style="margin-left: 4px; color: #666;">
                    <span>.</span><span>.</span><span>.</span>
                </span>
            </div>
        </div>
        <style>
            @keyframes blink {
                0%, 100% { opacity: 0; }
                50% { opacity: 1; }
            }
            .typing-dots span {
                animation: blink 1.4s infinite;
            }
            .typing-dots span:nth-child(2) {
                animation-delay: 0.2s;
            }
            .typing-dots span:nth-child(3) {
                animation-delay: 0.4s;
            }
        </style>
        """, unsafe_allow_html=True)
        
        try:
            response = st.session_state.assistant.query(query)
            typing_placeholder.empty()
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response
            })
        except Exception as e:
            typing_placeholder.empty()
            error_msg = f"I encountered an error: {str(e)}"
            st.session_state.messages.append({
                "role": "assistant", 
                "content": error_msg
            })
            log_error(f"Error processing query: {e}")
        
        st.rerun()
    
    if len(st.session_state.messages) > 0:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Clear Conversation", use_container_width=True):
                st.session_state.messages = []
                st.session_state.assistant.reset_conversation()
                st.rerun()

def main():
    try:
        display_sidebar()
        display_main_content()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        log_error(f"Application error: {e}")

if __name__ == "__main__":
    main()
