<script lang="ts">
  import { ArrowRight, Camera, ShieldCheck, CircleHelp } from '@lucide/svelte';
  import GlassCard from '../components/GlassCard.svelte';
  import HelpAccordion from '../components/HelpAccordion.svelte';
  let { onStart }: { onStart: () => void } = $props();
</script>
<div class="page-stack">
  <div class="page-intro"><div><p class="eyebrow">Guidance for every step</p><h2>A clearer process.<br /><em>A calmer experience.</em></h2><p>Know what to expect, what your recording contains, and what the current measurements can tell you.</p></div><CircleHelp class="intro-icon" size={68} strokeWidth={1} /></div>
  <div class="help-grid">
    <GlassCard><Camera size={26} /><h3>Before you begin</h3><HelpAccordion items={[
      { question: 'How should I position the camera?', answer: 'Place the camera on a stable surface with a clear view of your whole body, including your feet. Use even lighting and a clear, safe walking area. Confirm the framing in the live preview.' },
      { question: 'What happens when I click Camera?', answer: 'The Python backend looks for a readable USB camera and starts pose and hand tracking. Preview alone does not start CSV recording.' },
      { question: 'What if the camera does not connect?', answer: 'Check the USB cable, close other camera apps, and confirm the local backend is running. Then retry Camera. If several USB cameras are attached, disconnect the ones you do not intend to use.' },
      { question: 'Can I stop a test early?', answer: 'Yes. Save & stop closes the recording and releases the camera. Leaving Test Studio also requests a stop. Only detected pose samples are saved.' }
    ]} /></GlassCard>
    <GlassCard><ShieldCheck size={26} /><h3>Your data, explained</h3><HelpAccordion items={[
      { question: 'Are my camera videos stored?', answer: 'No video is saved by this recorder. It saves body landmark coordinates and timestamps in CSV files on this device. The default profile excludes face landmarks.' },
      { question: 'What do the FPS labels mean?', answer: 'Pose FPS and hand FPS report inference processing rates. They are not camera frame rate, measurement confidence, or clinical accuracy.' },
      { question: 'Why are some report tabs unavailable?', answer: 'Raw recording is connected. Joint angles, symmetry scores, and diagnostic interpretation require additional analysis and validation, so they remain explicitly uncalculated.' },
      { question: 'Is AI coaching active?', answer: 'No. Automated coaching is not connected to validated measurements yet. This page provides recording guidance, not personalized medical advice.' }
    ]} /></GlassCard>
  </div>
  <GlassCard class="help-cta"><div><p class="eyebrow">Whenever you are ready</p><h3>Make room for your next step.</h3></div><button class="primary-button" onclick={onStart}>Set up your camera <ArrowRight size={18} /></button></GlassCard>
</div>
