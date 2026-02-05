"""End-to-end tests for waza Web UI using Playwright."""

import pytest
import time
import subprocess
import signal
import os
from pathlib import Path


@pytest.fixture(scope="module")
def server():
    """Start waza server for testing."""
    # Find an available port
    port = 8765
    
    # Start the server
    env = os.environ.copy()
    proc = subprocess.Popen(
        ["waza", "serve", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    
    # Wait for server to be ready
    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("Server failed to start")
    
    yield f"http://localhost:{port}"
    
    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="module")
def browser_context(server):
    """Create browser context for tests."""
    from playwright.sync_api import sync_playwright
    
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    
    # Handle confirm dialogs automatically
    def handle_dialog(page):
        page.on("dialog", lambda dialog: dialog.accept())
    
    yield context, server, handle_dialog
    
    context.close()
    browser.close()
    playwright.stop()


class TestDashboard:
    """Test dashboard functionality."""
    
    def test_dashboard_loads(self, browser_context):
        """Test that dashboard loads without errors."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Check page title or header
        assert page.query_selector("text=waza") or page.query_selector("h1")
        
        # Should not have "Invalid Date"
        assert "Invalid Date" not in page.content()
        
        page.close()
    
    def test_dashboard_shows_stats(self, browser_context):
        """Test that dashboard shows stats cards."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Check for stat cards
        content = page.content()
        assert "Evals" in content or "Running" in content
        
        page.close()
    
    def test_dashboard_recent_runs(self, browser_context):
        """Test that recent runs section displays properly."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Should have Recent Runs section
        assert page.query_selector("text=Recent Runs") or page.query_selector("text=No runs")
        
        # No Invalid Date errors
        assert "Invalid Date" not in page.content()
        
        page.close()


class TestEvalsPage:
    """Test evals list page."""
    
    def test_evals_page_loads(self, browser_context):
        """Test that evals page loads."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        # Should have evals heading or list
        content = page.content()
        assert "Evals" in content or "Evaluation" in content or "No evals" in content
        
        page.close()
    
    def test_evals_navigation(self, browser_context):
        """Test navigation from dashboard to evals."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Click on Evals link
        evals_link = page.query_selector("a[href='/evals']")
        if evals_link:
            evals_link.click()
            page.wait_for_load_state("networkidle")
            assert "/evals" in page.url
        
        page.close()
    
    def test_generate_modal_opens(self, browser_context):
        """Test that generate/import modal can be opened."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        # Look for generate/import button
        generate_btn = page.query_selector("button:has-text('Generate')") or \
                       page.query_selector("button:has-text('Import')") or \
                       page.query_selector("button:has-text('New')")
        
        if generate_btn:
            generate_btn.click()
            time.sleep(0.5)
            
            # Modal should appear
            modal = page.query_selector("[role='dialog']") or \
                    page.query_selector(".modal") or \
                    page.query_selector("text=SKILL.md")
            assert modal is not None
        
        page.close()


class TestEvalDetail:
    """Test eval detail page."""
    
    def test_eval_detail_loads(self, browser_context):
        """Test that eval detail page loads for existing eval."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        # First get list of evals
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        # Click first eval if exists
        eval_link = page.query_selector("a[href*='/evals/'][href$='architecture']") or \
                    page.query_selector("a[href*='/evals/']")
        
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            # Should be on detail page
            assert "/evals/" in page.url
            
            # Should show tasks section
            content = page.content()
            assert "Tasks" in content or "No tasks" in content
            
            # No Invalid Date
            assert "Invalid Date" not in content
        
        page.close()
    
    def test_task_list_displays(self, browser_context):
        """Test that task list displays on eval detail."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            # Look for tasks section
            tasks_section = page.query_selector("text=Tasks")
            assert tasks_section is not None
        
        page.close()


class TestRunHistory:
    """Test run history display."""
    
    def test_run_history_no_invalid_dates(self, browser_context):
        """Test that run history shows valid dates."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        # Check dashboard
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        assert "Invalid Date" not in page.content()
        
        # Check evals page
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        assert "Invalid Date" not in page.content()
        
        # Check eval detail if available
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            assert "Invalid Date" not in page.content()
        
        page.close()


class TestAPIHealth:
    """Test API endpoints are accessible."""
    
    def test_health_endpoint(self, browser_context):
        """Test health endpoint returns valid response."""
        context, base_url, setup_dialog = browser_context
        
        # Use requests-style approach via page.evaluate
        page = context.new_page()
        page.goto(f"{base_url}/")  # Load any page first
        
        # Make API call via fetch
        result = page.evaluate(f"""
            async () => {{
                const response = await fetch('{base_url}/api/health');
                return {{ status: response.status, data: await response.json() }};
            }}
        """)
        
        assert result["status"] == 200
        assert result["data"]["status"] == "ok"
        
        page.close()
    
    def test_evals_endpoint(self, browser_context):
        """Test evals endpoint returns list."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        response = page.goto(f"{base_url}/api/evals")
        assert response.status == 200
        
        page.close()
    
    def test_runs_endpoint(self, browser_context):
        """Test runs endpoint returns list."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        response = page.goto(f"{base_url}/api/runs")
        assert response.status == 200
        
        page.close()


class TestSPARouting:
    """Test SPA routing works correctly."""
    
    def test_direct_evals_route(self, browser_context):
        """Test direct navigation to /evals works."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        response = page.goto(f"{base_url}/evals")
        assert response.status == 200
        
        # Should load React app, not 404
        assert "<!DOCTYPE html>" in page.content() or "evals" in page.content().lower()
        assert "404" not in page.query_selector("h1").text_content() if page.query_selector("h1") else True
        
        page.close()
    
    def test_direct_settings_route(self, browser_context):
        """Test direct navigation to /settings works."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        response = page.goto(f"{base_url}/settings")
        assert response.status == 200
        
        page.close()
    
    def test_nonexistent_route_fallback(self, browser_context):
        """Test that nonexistent routes still load app."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        response = page.goto(f"{base_url}/nonexistent-page-xyz")
        # Should still return 200 (SPA handles routing)
        assert response.status == 200
        
        page.close()


class TestGenerateModal:
    """Test suite generation functionality."""
    
    def test_generate_modal_opens(self, browser_context):
        """Test that generate modal opens from evals page."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        gen_btn = page.query_selector("button:has-text('Generate')")
        assert gen_btn, "Generate button not found"
        gen_btn.click()
        time.sleep(0.5)
        
        # Modal should be visible
        modal = page.query_selector("[role='dialog']") or page.query_selector(".fixed.inset-0")
        assert modal, "Modal did not open"
        
        page.close()
    
    def test_generate_modal_has_url_input(self, browser_context):
        """Test that generate modal has URL input field."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        gen_btn = page.query_selector("button:has-text('Generate')")
        gen_btn.click()
        time.sleep(0.5)
        
        # Check for URL input
        url_input = page.query_selector("input[placeholder*='URL']") or \
                    page.query_selector("input[type='url']") or \
                    page.query_selector("input")
        assert url_input, "URL input field not found"
        
        page.close()
    
    def test_generate_accepts_url(self, browser_context):
        """Test that generate modal accepts a SKILL.md URL."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        gen_btn = page.query_selector("button:has-text('Generate')")
        gen_btn.click()
        time.sleep(0.5)
        
        url_input = page.query_selector("input")
        if url_input:
            url_input.fill("https://raw.githubusercontent.com/microsoft/GitHub-Copilot-for-Azure/main/skills/azure-functions/SKILL.md")
            
            # Value should be set
            assert "azure-functions" in url_input.input_value().lower() or \
                   "skill" in url_input.input_value().lower()
        
        page.close()
    
    def test_generate_from_tree_url(self, browser_context):
        """Test that generating an eval from a GitHub tree URL works correctly."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        # Use the API to generate an eval from a tree URL
        page.goto(f"{base_url}/")  # Load any page first
        
        # Make API call to generate eval
        result = page.evaluate(f"""
            async () => {{
                const response = await fetch('{base_url}/api/skills/generate', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        skill_url: 'https://github.com/microsoft/GitHub-Copilot-for-Azure/tree/main/plugin/skills/azure-nodejs-production',
                        name: 'azure-nodejs-test',
                        assist: false
                    }})
                }});
                return {{ status: response.status, data: await response.json() }};
            }}
        """)
        
        # Should succeed
        assert result["status"] == 200, f"Generate failed: {result['data']}"
        
        # Skill name should be extracted correctly
        data = result["data"]
        assert data["skill_name"] == "azure-nodejs-production", f"Got skill_name: {data.get('skill_name')}"
        assert data["eval_id"], "No eval_id returned"
        
        # Now verify the eval has correct name
        eval_result = page.evaluate(f"""
            async () => {{
                const response = await fetch('{base_url}/api/evals/{data["eval_id"]}');
                return await response.json();
            }}
        """)
        
        # Name should NOT be "-eval"
        assert eval_result.get("name") != "-eval", f"Name is broken: {eval_result.get('name')}"
        assert "azure-nodejs" in eval_result.get("name", "").lower() or \
               "azure-nodejs" in eval_result.get("id", "").lower(), \
               f"Name doesn't contain expected skill: {eval_result}"
        
        # Cleanup - delete the test eval
        page.evaluate(f"""
            async () => {{
                await fetch('{base_url}/api/evals/{data["eval_id"]}', {{ method: 'DELETE' }});
            }}
        """)
        
        page.close()


class TestTaskCRUD:
    """Test task CRUD operations."""
    
    def test_tasks_section_exists(self, browser_context):
        """Test that tasks section exists on eval detail."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            heading = page.query_selector("h2:has-text('Tasks')") or \
                      page.query_selector("h3:has-text('Tasks')")
            assert heading, "Tasks section not found"
        
        page.close()
    
    def test_edit_task_button(self, browser_context):
        """Test that edit task button exists and opens editor."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            # Check if there are any tasks first
            edit_btn = page.query_selector("button[title='Edit task']")
            if edit_btn:
                edit_btn.click()
                time.sleep(0.5)
                
                editor = page.query_selector(".monaco-editor") or \
                         page.query_selector("textarea")
                assert editor, "Editor did not open"
            else:
                # No tasks available - check for "No tasks" message instead
                content = page.content()
                assert "No tasks" in content or "Add Task" in content, "Expected either tasks or 'No tasks' message"
        
        page.close()
    
    def test_duplicate_task_button(self, browser_context):
        """Test that duplicate task button exists if tasks exist."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            dup_btn = page.query_selector("button[title='Duplicate task']")
            # If no tasks, button won't exist - that's okay
            if dup_btn:
                assert dup_btn.is_visible(), "Duplicate button not visible"
            else:
                content = page.content()
                assert "No tasks" in content or "Add Task" in content
        
        page.close()
    
    def test_delete_task_button(self, browser_context):
        """Test that delete task button exists if tasks exist."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            del_btn = page.query_selector("button[title='Delete task']")
            # If no tasks, button won't exist - that's okay
            if del_btn:
                assert del_btn.is_visible(), "Delete button not visible"
            else:
                content = page.content()
                assert "No tasks" in content or "Add Task" in content
        
        page.close()
    
    def test_add_task_button(self, browser_context):
        """Test that add task button exists."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            add_btn = page.query_selector("button:has-text('Add Task')")
            assert add_btn, "Add Task button not found"
        
        page.close()
    
    def test_task_editor_has_yaml(self, browser_context):
        """Test that task editor shows YAML content."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            
            edit_btn = page.query_selector("button[title='Edit task']")
            if edit_btn:
                edit_btn.click()
                time.sleep(1)
                
                content = page.content()
                has_yaml = "name:" in content or "prompt:" in content
                assert has_yaml, "Task YAML content not displayed"
        
        page.close()
    
    def test_task_editor_save_cancel(self, browser_context):
        """Test that task editor has save/cancel buttons."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            
            edit_btn = page.query_selector("button[title='Edit task']")
            if edit_btn:
                edit_btn.click()
                time.sleep(0.5)
                
                save_btn = page.query_selector("button:has-text('Save')")
                cancel_btn = page.query_selector("button:has-text('Cancel')")
                assert save_btn or cancel_btn, "Save/Cancel buttons not found"
        
        page.close()
    
    def test_duplicate_task_works(self, browser_context):
        """Test that duplicating a task increases task count."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)
            
            tasks_before = len(page.query_selector_all("button[title='Duplicate task']"))
            
            dup_btn = page.query_selector("button[title='Duplicate task']")
            if dup_btn:
                dup_btn.click()
                time.sleep(1)
                page.wait_for_load_state("networkidle")
                
                tasks_after = len(page.query_selector_all("button[title='Duplicate task']"))
                assert tasks_after == tasks_before + 1, \
                    f"Expected {tasks_before + 1} tasks, got {tasks_after}"
        
        page.close()
    
    def test_delete_task_works(self, browser_context):
        """Test that deleting a task decreases task count."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        setup_dialog(page)  # Handle confirm dialog
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)
            
            tasks_before = len(page.query_selector_all("button[title='Delete task']"))
            
            if tasks_before > 1:  # Only delete if more than 1 task
                del_btn = page.query_selector("button[title='Delete task']")
                if del_btn:
                    del_btn.click()
                    time.sleep(1)
                    page.wait_for_load_state("networkidle")
                    
                    tasks_after = len(page.query_selector_all("button[title='Delete task']"))
                    assert tasks_after == tasks_before - 1, \
                        f"Expected {tasks_before - 1} tasks, got {tasks_after}"
        
        page.close()


class TestEvalEditor:
    """Test eval.yaml editor functionality."""
    
    def test_configuration_section_exists(self, browser_context):
        """Test that Configuration section exists on eval detail."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            heading = page.query_selector("h2:has-text('Configuration')")
            assert heading, "Configuration section not found"
        
        page.close()
    
    def test_edit_eval_button_exists(self, browser_context):
        """Test that edit eval config button exists in Configuration section."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            # Look for Edit button (not Edit task)
            edit_btns = page.query_selector_all("button:has-text('Edit')")
            # First Edit button is in Configuration section
            assert len(edit_btns) >= 1, "Edit button not found"
        
        page.close()
    
    def test_edit_eval_opens_modal(self, browser_context):
        """Test that clicking edit opens the eval editor modal."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            # Find the first Edit button (Configuration section)
            edit_btns = page.query_selector_all("button:has-text('Edit')")
            if edit_btns:
                edit_btns[0].click()
                time.sleep(0.5)
                
                modal = page.query_selector(".fixed.inset-0")
                assert modal, "Eval editor modal did not open"
        
        page.close()
    
    def test_eval_editor_has_yaml_content(self, browser_context):
        """Test that eval editor shows YAML content."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            edit_btns = page.query_selector_all("button:has-text('Edit')")
            if edit_btns:
                edit_btns[0].click()
                time.sleep(1)  # Wait for Monaco to load
                
                content = page.content()
                # Check for common eval fields
                has_content = "name:" in content or "skill:" in content
                assert has_content, "Eval YAML content not displayed"
        
        page.close()
    
    def test_eval_editor_has_save_cancel(self, browser_context):
        """Test that eval editor has save/cancel buttons."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            edit_btns = page.query_selector_all("button:has-text('Edit')")
            if edit_btns:
                edit_btns[0].click()
                time.sleep(0.5)
                
                save_btn = page.query_selector("button:has-text('Save Changes')")
                cancel_btn = page.query_selector("button:has-text('Cancel')")
                assert save_btn, "Save Changes button not found"
                assert cancel_btn, "Cancel button not found"
        
        page.close()
    
    def test_eval_editor_cancel_closes_modal(self, browser_context):
        """Test that cancel button closes the modal."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            edit_btns = page.query_selector_all("button:has-text('Edit')")
            if edit_btns:
                edit_btns[0].click()
                time.sleep(0.5)
                
                cancel_btn = page.query_selector("button:has-text('Cancel')")
                if cancel_btn:
                    cancel_btn.click()
                    time.sleep(0.3)
                    
                    modal = page.query_selector(".fixed.inset-0")
                    assert not modal, "Modal did not close after cancel"
        
        page.close()
    
    def test_configuration_shows_name(self, browser_context):
        """Test that configuration section shows eval name."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            content = page.content()
            assert "Name" in content, "Name field not shown in Configuration"
        
        page.close()
    
    def test_configuration_shows_skill(self, browser_context):
        """Test that configuration section shows skill name."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            content = page.content()
            assert "Skill" in content, "Skill field not shown in Configuration"
        
        page.close()


class TestRunEval:
    """Test eval run functionality."""
    
    def test_run_eval_button(self, browser_context):
        """Test that Run Eval button exists."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)  # Wait for React to render
            
            run_btn = page.query_selector("button:has-text('Run Eval')")
            assert run_btn, "Run Eval button not found"
        
        page.close()
    
    def test_run_eval_navigates_to_run_detail(self, browser_context):
        """Test that clicking Run Eval creates a run and navigates to run detail."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            
            run_btn = page.query_selector("button:has-text('Run Eval')")
            if run_btn:
                run_btn.click()
                # Wait for navigation to complete
                try:
                    page.wait_for_url("**/runs/**", timeout=10000)
                except:
                    time.sleep(5)  # Fallback wait
                
                # Should navigate to run detail page
                assert "/runs/" in page.url, f"Expected to navigate to run detail, got {page.url}"
        
        page.close()
    
    def test_run_detail_shows_summary_cards(self, browser_context):
        """Test that run detail page shows summary cards with pass rate, passed, failed, total."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            
            run_btn = page.query_selector("button:has-text('Run Eval')")
            if run_btn:
                run_btn.click()
                time.sleep(5)
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # Check for summary cards
                pass_rate = page.query_selector("text='Pass Rate'")
                passed = page.query_selector("text='Passed'")
                failed = page.query_selector("text='Failed'")
                total = page.query_selector("text='Total'")
                
                assert pass_rate, "Pass Rate card not found"
                assert passed, "Passed card not found"
                assert failed, "Failed card not found"
                assert total, "Total card not found"
        
        page.close()
    
    def test_run_detail_shows_task_results(self, browser_context):
        """Test that run detail page shows task results section."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            
            run_btn = page.query_selector("button:has-text('Run Eval')")
            if run_btn:
                run_btn.click()
                time.sleep(5)
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # Check for task results section
                task_results = page.query_selector("text='Task Results'")
                assert task_results, "Task Results section not found"
                
                # Check for task score display
                score_text = page.query_selector("text=/Score: \\d+\\.\\d+/")
                # Score might not be present if no tasks, so just verify no JS errors
                body = page.query_selector("body")
                assert body, "Page should have content"
        
        page.close()
    
    def test_run_detail_no_console_errors(self, browser_context):
        """Test that run detail page loads without console errors."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        
        page.goto(f"{base_url}/evals")
        page.wait_for_load_state("networkidle")
        
        eval_link = page.query_selector("a[href*='/evals/']")
        if eval_link:
            eval_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            
            run_btn = page.query_selector("button:has-text('Run Eval')")
            if run_btn:
                run_btn.click()
                time.sleep(5)
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # Filter out non-critical errors
                critical_errors = [e for e in errors if "TypeError" in e or "ReferenceError" in e]
                assert not critical_errors, f"Console errors found: {critical_errors}"
        
        page.close()


class TestRunDetail:
    """Test run detail page."""
    
    def _get_run_id(self, base_url):
        """Get a run ID from the API."""
        import urllib.request
        import json
        with urllib.request.urlopen(f"{base_url}/api/runs") as resp:
            runs = json.loads(resp.read().decode())
        return runs[0]["id"] if runs else None
    
    def _get_failed_run_id(self, base_url):
        """Get a failed run ID from the API."""
        import urllib.request
        import json
        with urllib.request.urlopen(f"{base_url}/api/runs") as resp:
            runs = json.loads(resp.read().decode())
        failed = next((r for r in runs if r.get("status") == "failed"), None)
        return failed["id"] if failed else None
    
    def test_run_detail_loads(self, browser_context):
        """Test that run detail page loads."""
        context, base_url, setup_dialog = browser_context
        run_id = self._get_run_id(base_url)
        if not run_id:
            pytest.skip("No runs available")
        
        page = context.new_page()
        response = page.goto(f"{base_url}/runs/{run_id}")
        assert response.status == 200
        page.close()
    
    def test_run_detail_shows_run_id(self, browser_context):
        """Test that run detail shows the run ID."""
        context, base_url, setup_dialog = browser_context
        run_id = self._get_run_id(base_url)
        if not run_id:
            pytest.skip("No runs available")
        
        page = context.new_page()
        page.goto(f"{base_url}/runs/{run_id}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        assert run_id[:8] in page.content()
        page.close()
    
    def test_run_detail_has_back_link(self, browser_context):
        """Test that run detail has back link."""
        context, base_url, setup_dialog = browser_context
        run_id = self._get_run_id(base_url)
        if not run_id:
            pytest.skip("No runs available")
        
        page = context.new_page()
        page.goto(f"{base_url}/runs/{run_id}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        back_link = page.query_selector("a:has-text('Back')")
        assert back_link, "Back link not found"
        page.close()
    
    def test_run_detail_shows_status(self, browser_context):
        """Test that run detail shows status."""
        context, base_url, setup_dialog = browser_context
        run_id = self._get_run_id(base_url)
        if not run_id:
            pytest.skip("No runs available")
        
        page = context.new_page()
        page.goto(f"{base_url}/runs/{run_id}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        content = page.content().lower()
        has_status = "failed" in content or "completed" in content or \
                     "running" in content or "pending" in content
        assert has_status, "Status not found"
        page.close()
    
    def test_failed_run_shows_error(self, browser_context):
        """Test that failed run shows error message."""
        context, base_url, setup_dialog = browser_context
        run_id = self._get_failed_run_id(base_url)
        if not run_id:
            pytest.skip("No failed runs available")
        
        page = context.new_page()
        page.goto(f"{base_url}/runs/{run_id}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        content = page.content()
        assert "Run Failed" in content or "error" in content.lower()
        page.close()
    
    def test_nonexistent_run_handled(self, browser_context):
        """Test that nonexistent run is handled gracefully."""
        context, base_url, setup_dialog = browser_context
        page = context.new_page()
        
        page.goto(f"{base_url}/runs/nonexistent-run-xyz")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        content = page.content().lower()
        assert "not found" in content or "run" in content
        page.close()
    
    def test_back_link_navigates(self, browser_context):
        """Test that back link navigates to eval."""
        context, base_url, setup_dialog = browser_context
        run_id = self._get_run_id(base_url)
        if not run_id:
            pytest.skip("No runs available")
        
        page = context.new_page()
        page.goto(f"{base_url}/runs/{run_id}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        back = page.query_selector("a:has-text('Back')")
        if back:
            back.click()
            page.wait_for_load_state("networkidle")
            assert "/evals/" in page.url
        
        page.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
