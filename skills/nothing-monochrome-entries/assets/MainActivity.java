package ENTRY_PACKAGE;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;

/** A normal launcher activity that forwards to the original app, then finishes. */
public final class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Intent target = new Intent(Intent.ACTION_MAIN)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .setComponent(new ComponentName(EntryTarget.PACKAGE, EntryTarget.ACTIVITY))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
        try {
            startActivity(target);
        } catch (ActivityNotFoundException | SecurityException unavailable) {
            Toast.makeText(this, "Unable to open " + EntryTarget.LABEL, Toast.LENGTH_LONG).show();
        } finally {
            finish();
        }
    }
}
