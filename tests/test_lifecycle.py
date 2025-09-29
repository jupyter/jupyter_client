"""
Unit tests for jupyter_client.lifecycle module
"""
import pytest
from unittest.mock import Mock
from traitlets import HasTraits

from jupyter_client.lifecycle import (
    LifecycleState,
    KernelManagerStateMixin,
    state_transition
)


class TestLifecycleState:
    """Test cases for LifecycleState enum"""

    def test_enum_values(self):
        """Test that enum values are correct strings"""
        assert LifecycleState.UNKNOWN == "unknown"
        assert LifecycleState.STARTING == "starting"
        assert LifecycleState.STARTED == "started"
        assert LifecycleState.RESTARTING == "restarting"
        assert LifecycleState.RESTARTED == "restarted"
        assert LifecycleState.TERMINATING == "terminating"
        assert LifecycleState.DEAD == "dead"

    def test_enum_string_behavior(self):
        """Test that enum inherits from str and behaves like strings"""
        assert isinstance(LifecycleState.UNKNOWN, str)
        assert LifecycleState.UNKNOWN == "unknown"
        assert "unknown" == LifecycleState.UNKNOWN
        # Note: str() returns the enum name, but direct comparison works
        assert LifecycleState.STARTING == "starting"

    def test_enum_comparison(self):
        """Test enum value comparisons"""
        assert LifecycleState.UNKNOWN != LifecycleState.STARTING
        assert LifecycleState.STARTED == LifecycleState.STARTED
        assert LifecycleState.DEAD == "dead"


class TestStateTransitionDecorator:
    """Test cases for state_transition decorator"""

    def test_sync_method_success(self):
        """Test state transition decorator with sync method - success case"""
        class TestManager(HasTraits):
            lifecycle_state = LifecycleState.UNKNOWN

            @state_transition(LifecycleState.STARTING, LifecycleState.STARTED)
            def start_method(self):
                return "success"

        manager = TestManager()
        result = manager.start_method()

        assert result == "success"
        assert manager.lifecycle_state == LifecycleState.STARTED

    def test_sync_method_failure(self):
        """Test state transition decorator with sync method - failure case"""
        class TestManager(HasTraits):
            lifecycle_state = LifecycleState.UNKNOWN

            @state_transition(LifecycleState.STARTING, LifecycleState.STARTED)
            def failing_method(self):
                raise ValueError("Test error")

        manager = TestManager()

        with pytest.raises(ValueError):
            manager.failing_method()

        assert manager.lifecycle_state == LifecycleState.UNKNOWN

    @pytest.mark.asyncio
    async def test_async_method_success(self):
        """Test state transition decorator with async method - success case"""
        class TestManager(HasTraits):
            lifecycle_state = LifecycleState.UNKNOWN

            @state_transition(LifecycleState.STARTING, LifecycleState.STARTED)
            async def async_start_method(self):
                return "async_success"

        manager = TestManager()
        result = await manager.async_start_method()

        assert result == "async_success"
        assert manager.lifecycle_state == LifecycleState.STARTED

    @pytest.mark.asyncio
    async def test_async_method_failure(self):
        """Test state transition decorator with async method - failure case"""
        class TestManager(HasTraits):
            lifecycle_state = LifecycleState.UNKNOWN

            @state_transition(LifecycleState.STARTING, LifecycleState.STARTED)
            async def async_failing_method(self):
                raise RuntimeError("Async test error")

        manager = TestManager()

        with pytest.raises(RuntimeError):
            await manager.async_failing_method()

        assert manager.lifecycle_state == LifecycleState.UNKNOWN

    def test_state_transition_sequence(self):
        """Test that state transitions happen in correct order"""
        states_seen = []

        class TestManager(HasTraits):
            _lifecycle_state = LifecycleState.UNKNOWN

            @property
            def lifecycle_state(self):
                return self._lifecycle_state

            @lifecycle_state.setter
            def lifecycle_state(self, value):
                states_seen.append(value)
                self._lifecycle_state = value

            @state_transition(LifecycleState.STARTING, LifecycleState.STARTED)
            def start_method(self):
                states_seen.append("method_called")
                return "done"

        manager = TestManager()
        manager.start_method()

        # Should see: STARTING (before method), method_called, STARTED (after method)
        assert states_seen == [LifecycleState.STARTING, "method_called", LifecycleState.STARTED]


class TestKernelManagerStateMixin:
    """Test cases for KernelManagerStateMixin"""

    def test_mixin_initialization(self):
        """Test that mixin initializes with correct default state"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            pass

        manager = TestManager()
        assert manager.lifecycle_state == LifecycleState.UNKNOWN

    def test_state_properties(self):
        """Test state check properties"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            pass

        manager = TestManager()

        # Test initial unknown state
        assert manager.is_unknown
        assert not manager.is_starting
        assert not manager.is_started
        assert not manager.is_restarting
        assert not manager.is_restarted
        assert not manager.is_terminating
        assert not manager.is_dead

        # Test starting state
        manager.lifecycle_state = LifecycleState.STARTING
        assert not manager.is_unknown
        assert manager.is_starting
        assert not manager.is_started

        # Test started state
        manager.lifecycle_state = LifecycleState.STARTED
        assert not manager.is_starting
        assert manager.is_started
        assert not manager.is_dead

        # Test dead state
        manager.lifecycle_state = LifecycleState.DEAD
        assert not manager.is_started
        assert manager.is_dead

    def test_set_lifecycle_state(self):
        """Test manual state setting"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            pass

        manager = TestManager()
        manager.set_lifecycle_state(LifecycleState.STARTED)

        assert manager.lifecycle_state == LifecycleState.STARTED
        assert manager.is_started

    def test_lifecycle_state_observer(self):
        """Test that state changes are logged"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            def __init__(self):
                super().__init__()
                self.log = Mock()

        manager = TestManager()
        manager.kernel_id = "test-kernel-123"

        # Change state to trigger observer
        manager.lifecycle_state = LifecycleState.STARTING

        # Check that log.debug was called
        manager.log.debug.assert_called_once()
        call_args = manager.log.debug.call_args[0][0]
        assert "test-kernel-123" in call_args
        # The actual log format shows enum representation
        assert "LifecycleState.UNKNOWN -> LifecycleState.STARTING" in call_args

    def test_automatic_method_wrapping_start_kernel(self):
        """Test that start_kernel is automatically wrapped with state transitions"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            def start_kernel(self):
                return "kernel_started"

        manager = TestManager()
        assert manager.lifecycle_state == LifecycleState.UNKNOWN

        result = manager.start_kernel()

        assert result == "kernel_started"
        assert manager.lifecycle_state == LifecycleState.STARTED

    @pytest.mark.asyncio
    async def test_automatic_method_wrapping_async_start_kernel(self):
        """Test that async start_kernel is automatically wrapped"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            async def start_kernel(self):
                return "async_kernel_started"

        manager = TestManager()
        assert manager.lifecycle_state == LifecycleState.UNKNOWN

        result = await manager.start_kernel()

        assert result == "async_kernel_started"
        assert manager.lifecycle_state == LifecycleState.STARTED

    def test_automatic_method_wrapping_restart_kernel(self):
        """Test that restart_kernel is automatically wrapped"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            def restart_kernel(self):
                return "kernel_restarted"

        manager = TestManager()
        manager.lifecycle_state = LifecycleState.STARTED  # Set initial state

        result = manager.restart_kernel()

        assert result == "kernel_restarted"
        assert manager.lifecycle_state == LifecycleState.RESTARTED

    def test_automatic_method_wrapping_shutdown_kernel(self):
        """Test that shutdown_kernel is automatically wrapped"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            def shutdown_kernel(self):
                return "kernel_shutdown"

        manager = TestManager()
        manager.lifecycle_state = LifecycleState.STARTED  # Set initial state

        result = manager.shutdown_kernel()

        assert result == "kernel_shutdown"
        assert manager.lifecycle_state == LifecycleState.DEAD

    def test_method_wrapping_failure_handling(self):
        """Test that method failures set state to UNKNOWN"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            def start_kernel(self):
                raise Exception("Start failed")

        manager = TestManager()

        with pytest.raises(Exception):
            manager.start_kernel()

        assert manager.lifecycle_state == LifecycleState.UNKNOWN

    def test_mixin_with_inheritance(self):
        """Test that mixin works correctly with complex inheritance"""
        class BaseManager(HasTraits):
            def base_method(self):
                return "base"

        class TestManager(KernelManagerStateMixin, BaseManager):
            def start_kernel(self):
                return "started"

            def restart_kernel(self):
                return "restarted"

            def shutdown_kernel(self):
                return "shutdown"

        manager = TestManager()

        # Test base functionality still works
        assert manager.base_method() == "base"

        # Test state transitions work
        assert manager.lifecycle_state == LifecycleState.UNKNOWN

        manager.start_kernel()
        assert manager.lifecycle_state == LifecycleState.STARTED

        manager.restart_kernel()
        assert manager.lifecycle_state == LifecycleState.RESTARTED

        manager.shutdown_kernel()
        assert manager.lifecycle_state == LifecycleState.DEAD

    def test_mixin_without_kernel_methods(self):
        """Test that mixin works even when kernel methods don't exist"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            def some_other_method(self):
                return "other"

        # Should not raise any errors during class creation
        manager = TestManager()
        assert manager.lifecycle_state == LifecycleState.UNKNOWN
        assert manager.some_other_method() == "other"

    def test_state_transitions_complete_lifecycle(self):
        """Test a complete kernel lifecycle with state transitions"""
        class TestManager(KernelManagerStateMixin, HasTraits):
            def start_kernel(self):
                return "started"

            def restart_kernel(self):
                return "restarted"

            def shutdown_kernel(self):
                return "shutdown"

        manager = TestManager()

        # Initial state
        assert manager.is_unknown

        # Start kernel
        manager.start_kernel()
        assert manager.is_started
        assert not manager.is_unknown

        # Restart kernel
        manager.restart_kernel()
        assert manager.is_restarted
        assert not manager.is_started

        # Shutdown kernel
        manager.shutdown_kernel()
        assert manager.is_dead
        assert not manager.is_restarted


class TestJupyterClientIntegration:
    """Test integration with jupyter_client patterns"""

    def test_with_mock_kernel_manager_interface(self):
        """Test mixin works with typical KernelManager interface"""

        class MockKernelManager(KernelManagerStateMixin, HasTraits):
            """Mock kernel manager following jupyter_client patterns"""

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.kernel_id = "test-kernel-123"
                self.log = Mock()

            def start_kernel(self, **kwargs):
                """Mock start_kernel method"""
                return {"kernel_id": self.kernel_id}

            async def restart_kernel(self, **kwargs):
                """Mock async restart_kernel method"""
                return {"kernel_id": self.kernel_id}

            def shutdown_kernel(self, immediate=False, **kwargs):
                """Mock shutdown_kernel method"""
                return True

        manager = MockKernelManager()

        # Test initial state
        assert manager.is_unknown

        # Test start
        result = manager.start_kernel()
        assert result["kernel_id"] == "test-kernel-123"
        assert manager.is_started

        # Test restart
        import asyncio
        async def test_restart():
            result = await manager.restart_kernel()
            assert result["kernel_id"] == "test-kernel-123"
            assert manager.is_restarted

        asyncio.run(test_restart())

        # Test shutdown
        result = manager.shutdown_kernel(immediate=True)
        assert result is True
        assert manager.is_dead

    def test_configurable_lifecycle_state(self):
        """Test that lifecycle_state is properly configurable"""

        class ConfigurableManager(KernelManagerStateMixin, HasTraits):
            pass

        # Test default configuration
        manager = ConfigurableManager()
        assert manager.lifecycle_state == LifecycleState.UNKNOWN

        # Test configuration override
        manager_configured = ConfigurableManager(lifecycle_state="started")
        assert manager_configured.lifecycle_state == "started"
        assert manager_configured.is_started