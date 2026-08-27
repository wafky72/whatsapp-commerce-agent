<?php
/**
 * Plugin Name: rzb AI Chat Assistant
 * Plugin URI: https://yourwebsite.com
 * Description: Professional AI-powered chat assistant for your WooCommerce store. Handles product queries, order tracking, and customer support automatically.
 * Version: 1.0.0
 * Author: Kannan
 * Author URI: https://yourwebsite.com
 * License: GPL-2.0+
 * Text Domain: rzb-ai-chat
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

class Roze_AI_Chat {
    
    private $api_endpoint;
    
    public function __construct() {
        // Default to localhost - user will configure this
        $this->api_endpoint = get_option('roze_chat_api_endpoint', 'http://localhost:8002');
        
        // Hooks
        add_action('wp_footer', array($this, 'render_chat_widget'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
    }
    
    /**
     * Render the chat widget in frontend
     */
    public function render_chat_widget() {
        // Check if widget is enabled
        if (!get_option('roze_chat_enabled', true)) {
            return;
        }
        
        // Check if on mobile and hidden
        $hide_mobile = get_option('roze_chat_hide_mobile', false);
        if ($hide_mobile && wp_is_mobile()) {
            return;
        }
        
        ?>
        <!-- Roze AI Chat Widget -->
        <script>
            window.RozeChatConfig = {
                apiEndpoint: '<?php echo esc_js($this->api_endpoint); ?>'
            };
        </script>
        <script src="<?php echo esc_url($this->api_endpoint . '/widget/chat-widget.js'); ?>" defer></script>
        <?php
    }
    
    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_menu_page(
            'Roze AI Chat',
            'AI Chat',
            'manage_options',
            'roze-ai-chat',
            array($this, 'render_admin_page'),
            'dashicons-format-chat',
            30
        );
    }
    
    /**
     * Register plugin settings
     */
    public function register_settings() {
        register_setting('roze_chat_settings', 'roze_chat_enabled');
        register_setting('roze_chat_settings', 'roze_chat_api_endpoint');
        register_setting('roze_chat_settings', 'roze_chat_hide_mobile');
    }
    
    /**
     * Render admin settings page
     */
    public function render_admin_page() {
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            
            <div class="notice notice-info">
                <p><strong>🎉 Quick Setup:</strong> Your AI Chat Assistant is almost ready!</p>
            </div>
            
            <div class="card" style="max-width: 800px; padding: 20px; margin-top: 20px;">
                <h2>⚙️ Configuration</h2>
                
                <form method="post" action="options.php">
                    <?php settings_fields('roze_chat_settings'); ?>
                    
                    <table class="form-table">
                        <tr>
                            <th scope="row">
                                <label for="roze_chat_enabled">Enable Chat Widget</label>
                            </th>
                            <td>
                                <input 
                                    type="checkbox" 
                                    id="roze_chat_enabled" 
                                    name="roze_chat_enabled" 
                                    value="1" 
                                    <?php checked(get_option('roze_chat_enabled', true), 1); ?>
                                >
                                <p class="description">Show the AI chat widget on your website</p>
                            </td>
                        </tr>
                        
                        <tr>
                            <th scope="row">
                                <label for="roze_chat_api_endpoint">API Endpoint</label>
                            </th>
                            <td>
                                <input 
                                    type="url" 
                                    id="roze_chat_api_endpoint" 
                                    name="roze_chat_api_endpoint" 
                                    value="<?php echo esc_attr(get_option('roze_chat_api_endpoint', 'http://localhost:8002')); ?>"
                                    class="regular-text"
                                    placeholder="http://localhost:8002"
                                    required
                                >
                                <p class="description">
                                    The URL where your AI backend is running.<br>
                                    <strong>For localhost:</strong> http://localhost:8002<br>
                                    <strong>For production:</strong> https://your-domain.com/api
                                </p>
                            </td>
                        </tr>
                        
                        <tr>
                            <th scope="row">
                                <label for="roze_chat_hide_mobile">Hide on Mobile</label>
                            </th>
                            <td>
                                <input 
                                    type="checkbox" 
                                    id="roze_chat_hide_mobile" 
                                    name="roze_chat_hide_mobile" 
                                    value="1" 
                                    <?php checked(get_option('roze_chat_hide_mobile', false), 1); ?>
                                >
                                <p class="description">Don't show chat widget on mobile devices</p>
                            </td>
                        </tr>
                    </table>
                    
                    <?php submit_button(); ?>
                </form>
            </div>
            
            <div class="card" style="max-width: 800px; padding: 20px; margin-top: 20px; background: #f0f6fc;">
                <h2>🎨 Advanced Customization</h2>
                <p>For advanced settings like colors, position, welcome message, and AI configuration:</p>
                <a href="<?php echo esc_url($this->api_endpoint . '/admin'); ?>" 
                   class="button button-primary button-large" 
                   target="_blank" 
                   style="margin-top: 10px;">
                    Open Advanced Settings Dashboard →
                </a>
                <p class="description" style="margin-top: 15px;">
                    This opens the full admin panel where you can customize appearance, behavior, and AI settings.
                </p>
            </div>
            
            <div class="card" style="max-width: 800px; padding: 20px; margin-top: 20px;">
                <h2>📊 Analytics & Performance</h2>
                <p>View conversation analytics, popular questions, and performance metrics:</p>
                <a href="<?php echo esc_url($this->api_endpoint . '/admin#analytics'); ?>" 
                   class="button button-secondary" 
                   target="_blank">
                    View Analytics Dashboard →
                </a>
            </div>
            
            <div class="card" style="max-width: 800px; padding: 20px; margin-top: 20px;">
                <h2>🧪 Test Your Chat</h2>
                <p>Test the AI assistant before going live:</p>
                <a href="<?php echo esc_url($this->api_endpoint . '/test'); ?>" 
                   class="button button-secondary" 
                   target="_blank">
                    Open Test Interface →
                </a>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: white; border-left: 4px solid #0073aa;">
                <h3>📚 Quick Setup Guide</h3>
                <ol style="line-height: 1.8;">
                    <li><strong>Start the Backend:</strong> Run <code>python -m uvicorn main:app --reload --port 8002</code></li>
                    <li><strong>Configure API Endpoint:</strong> Enter your backend URL above and Save Changes</li>
                    <li><strong>Customize Appearance:</strong> Click "Open Advanced Settings Dashboard" to configure colors, position, etc.</li>
                    <li><strong>Test:</strong> Use the Test Interface to verify everything works</li>
                    <li><strong>Go Live:</strong> Enable the widget and it will appear on your site!</li>
                </ol>
            </div>
        </div>
        
        <style>
            .roze-chat-card {
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        </style>
        <?php
    }
}

// Initialize the plugin
function roze_ai_chat_init() {
    new Roze_AI_Chat();
}
add_action('plugins_loaded', 'roze_ai_chat_init');

// Activation hook
register_activation_hook(__FILE__, 'roze_ai_chat_activate');
function roze_ai_chat_activate() {
    // Set default options
    add_option('roze_chat_enabled', true);
    add_option('roze_chat_api_endpoint', 'http://localhost:8002');
    add_option('roze_chat_hide_mobile', false);
}

// Deactivation hook
register_deactivation_hook(__FILE__, 'roze_ai_chat_deactivate');
function roze_ai_chat_deactivate() {
    // Clean up if needed
}
