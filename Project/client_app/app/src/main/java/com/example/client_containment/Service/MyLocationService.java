package com.example.client_containment.Service;

import static com.example.client_containment.MainActivity.cacheLocation;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.location.Location;
import android.util.Log;
import android.widget.Toast;

import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonArrayRequest;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.RequestFuture;
import com.android.volley.toolbox.Volley;
import com.example.client_containment.MainActivity;
import com.google.android.gms.location.LocationResult;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Locale;

public class MyLocationService extends BroadcastReceiver {
    public static final String ACTION_PROCESS_UPDATE = "com.example.client_containment.Service.UPDATE_LOCATION";

    @Override // android.content.BroadcastReceiver
    public void onReceive(Context context, Intent intent) {
        LocationResult result;
        if (intent != null) {
            String action = intent.getAction();
            if (ACTION_PROCESS_UPDATE.equals(action) && (result = LocationResult.extractResult(intent)) != null) {
                Location location = result.getLastLocation();
                String loc = String.format(Locale.getDefault(), "%.2f", location.getLatitude()) + "/" + String.format(Locale.getDefault(), "%.2f", location.getLongitude());
                if (cacheLocation.equals(loc)) return;
                cacheLocation = loc;
                try {
                    MainActivity.getInstance().updateTextView(loc);
                    postDataUsingVolley(String.format(Locale.getDefault(), "%.2f", location.getLatitude()), String.format(Locale.getDefault(), "%.2f", location.getLongitude()), context);
                    getDataUsingVolley(context, location);
                } catch (Exception e) {
                    Toast.makeText(context, loc, Toast.LENGTH_SHORT).show();
                }
            }
        }
    }

    private void getDataUsingVolley(final Context context, final Location location) {
        final SharedPreferences sharedPreferences = context.getSharedPreferences("user_data", 0);
        ArrayList<Location> locationList = new ArrayList<>();
        RequestQueue queue = Volley.newRequestQueue(context);
        RequestFuture.newFuture();
        // from class: com.example.client_containment.Service.MyLocationService.1
// com.android.volley.Response.Listener
        JsonArrayRequest jsonObjReq = new JsonArrayRequest(0, MainActivity.BASE_URL + "location_data", null, response -> {
            for (int locationIndex = 0; locationIndex < response.length(); locationIndex++) {
                try {
                    JSONObject j = response.getJSONObject(locationIndex);
                    Log.d("TAG", "getDataUsingVolley: " + j);
                    Location l = new Location("");
                    l.setLatitude(j.getDouble("location_lat"));
                    l.setLongitude(j.getDouble("location_long"));
                    int locationId = j.getInt("id");
                    double latitude = Double.parseDouble(sharedPreferences.getString("latitudeVisited", "0"));
                    double longitude = Double.parseDouble(sharedPreferences.getString("longitudeVisited", "0"));
                    Location alreadyVisited = new Location("");
                    alreadyVisited.setLongitude(longitude);
                    alreadyVisited.setLatitude(latitude);
                    if (l.distanceTo(alreadyVisited) != 0.0f) {
                        float distanceInMeters = l.distanceTo(location);
                        Log.d("dis", String.valueOf(distanceInMeters));
                        if (distanceInMeters < 100.0f) {
                            MyLocationService.this.sendMailUsingVolley(context, locationId);
                            SharedPreferences.Editor editor = sharedPreferences.edit();
                            editor.putString("latitudeVisited", String.format(Locale.getDefault(), "%.2f", l.getLatitude()));
                            editor.putString("longitudeVisited", String.format(Locale.getDefault(), "%.2f", l.getLongitude()));
                            editor.apply();
                        }
                    }
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        }, VolleyResponseImpl.INSTANCE);
        Log.d("lllist", locationList.toString());
        queue.add(jsonObjReq);
    }

    private void postDataUsingVolley(String lat, String lon, Context context) {
        RequestQueue queue = Volley.newRequestQueue(context);
        SharedPreferences sharedPreferences = context.getSharedPreferences("user_data", 0);
        int id = sharedPreferences.getInt("id", 0);
        JSONObject postparams = new JSONObject();
        try {
            postparams.put("id", id);
            postparams.put("lat", lat);
            postparams.put("long", lon);
            postparams.put("timestamp", Calendar.getInstance().getTime().toString());
        } catch (JSONException e) {
            e.printStackTrace();
        }
        JsonObjectRequest jsonObjReq = new JsonObjectRequest(1, MainActivity.BASE_URL + "post_user_location_data", postparams, response -> Log.d("response", response.toString()), error -> Log.d("error", error.toString()));
        queue.add(jsonObjReq);
    }

    public void sendMailUsingVolley(Context context, int locationId) {
        RequestQueue queue = Volley.newRequestQueue(context);
        SharedPreferences sharedPreferences = context.getSharedPreferences("user_data", 0);
        String email = sharedPreferences.getString("email", "null");
        JSONObject postparams = new JSONObject();
        try {
            postparams.put("email", email);
            postparams.put("id", locationId);
        } catch (JSONException e) {
            e.printStackTrace();
        }
        JsonObjectRequest jsonObjReq = new JsonObjectRequest(1, MainActivity.BASE_URL + "send_trigger", postparams, response -> Log.d("response", response.toString()), error -> Log.d("error", error.toString()));
        queue.add(jsonObjReq);
    }
}

final class VolleyResponseImpl implements Response.ErrorListener {
    public static final VolleyResponseImpl INSTANCE = new VolleyResponseImpl();

    private VolleyResponseImpl() {
    }

    @Override
    public void onErrorResponse(VolleyError volleyError) {
        Log.d("error", volleyError.toString());
    }
}